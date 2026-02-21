from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models.interview import Interview
from app.models.interview_evaluation import InterviewEvaluation
from app.models.job_application import JobApplication, ApplicationStatus, FinalResult
from app.models.job import Job
from app.models.resume import Resume
from app.models.suitability import CandidateJobSuitability
from app.models.user import Candidate, User
from app.schemas.application import ApplicationReviewRequest, FinalResultRequest
from app.services.application import create_application, schedule_interview
from app.api.auth import get_current_candidate, get_current_recruiter

router = APIRouter()

@router.post("/candidate/apply/{job_id}")
async def apply_for_job(
    job_id: int, 
    db: Session = Depends(get_db),
    current_candidate: User = Depends(get_current_candidate)
):
    # Check if job exists
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if suitability score exists and is above 50
    suitability = db.query(CandidateJobSuitability).filter(
        CandidateJobSuitability.candidate_id == current_candidate.id,
        CandidateJobSuitability.job_id == job_id
    ).first()

    if not suitability or suitability.suitability_score < 50:
        raise HTTPException(status_code=400, detail="Not eligible to apply for this job")

    # Check if the candidate already applied
    existing_application = db.query(JobApplication).filter(
        JobApplication.candidate_id == current_candidate.id,
        JobApplication.job_id == job_id
    ).first()
    if existing_application:
        raise HTTPException(status_code=400, detail="Already applied for this job")

    # Create application
    application = create_application(db, current_candidate.id, job_id)

    if suitability.suitability_score > 50:
        try:
            interview_link = await schedule_interview(current_candidate, job, application.application_id, db)
            application.status = ApplicationStatus.INTERVIEW_SCHEDULED
            db.commit()
            return {"message": "Interview scheduled automatically", "interview_link": interview_link}
        except Exception as e:
            db.rollback()
            db.delete(application)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to schedule interview: {str(e)}")

    return {"message": "Application sent for recruiter review."}

@router.get("/candidate/my-applications")
def get_candidate_applications(
    db: Session = Depends(get_db),
    current_candidate: User = Depends(get_current_candidate)
):
    """
    Returns all applications submitted by the currently logged-in candidate,
    including job details and application status.
    """
    applications = (
        db.query(
            JobApplication,
            Job.title,
            Job.company_name,
            Job.location,
            Job.time,
            CandidateJobSuitability.suitability_score
        )
        .join(Job, JobApplication.job_id == Job.job_id)
        .outerjoin(
            CandidateJobSuitability,
            and_(
                CandidateJobSuitability.job_id == JobApplication.job_id,
                CandidateJobSuitability.candidate_id == JobApplication.candidate_id
            )
        )
        .filter(JobApplication.candidate_id == current_candidate.id)
        .all()
    )
    
    return [
        {
            "application_id": app.JobApplication.application_id,
            "job_title": app.title,
            "company_name": app.company_name,
            "job_location": app.location,
            "job_type": app.time,
            "status": app.JobApplication.status,
            "suitability_score": app.suitability_score,
            "applied_at": app.JobApplication.applied_at,
            "interview_scheduled": app.JobApplication.status == ApplicationStatus.INTERVIEW_SCHEDULED,
            "interview_link": f"http://127.0.0.1:3000/interview/{app.JobApplication.application_id}" 
                if app.JobApplication.status == ApplicationStatus.INTERVIEW_SCHEDULED else None
        }
        for app in applications
    ]

@router.get("/candidate/application/{application_id}/result")
def get_application_result(
    application_id: int,
    db: Session = Depends(get_db),
    current_candidate: User = Depends(get_current_candidate)
):
    """
    Allows candidates to check the final result of their application
    """
    # Get the application
    application = db.query(JobApplication).filter(
        JobApplication.application_id == application_id,
        JobApplication.candidate_id == current_candidate.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get job details
    job = db.query(Job).filter(Job.job_id == application.job_id).first()
    
    final_result = "Pending"
    if application.final_result and application.final_result != FinalResult.PENDING:
        final_result = application.final_result.value
    
    return {
        "application_id": application.application_id,
        "job_title": job.title,
        "company_name": job.company_name,
        "status": application.status.value,
        "final_result": final_result,
        "feedback": application.feedback if hasattr(application, 'feedback') else None,
        "applied_at": application.applied_at
    }

@router.post("/recruiter/review/{application_id}")
async def review_application(
    application_id: int,
    review: ApplicationReviewRequest,
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter),
):
    # Fetch the job application
    application = db.query(JobApplication).filter(
        JobApplication.application_id == application_id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Verify if the recruiter owns the job
    if application.job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=403, detail="You are not authorized to review this application"
        )

    # Check if application is in pending status
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="This application has already been reviewed"
        )

    # Process the review decision
    if review.decision.lower() == "approved":
        application.status = ApplicationStatus.INTERVIEW_SCHEDULED
        interview_link = await schedule_interview(application.candidate, application.job,application.application_id, db)

        message = "Application approved. Interview scheduled."
    else:
        application.status = ApplicationStatus.REJECTED
        message = "Application rejected."

    db.commit()
    return {"message": message, "application_status": application.status}

@router.get("/recruiter/applications")
def get_all_applications(
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    # Get all applications for jobs posted by this recruiter
    applications = (
        db.query(JobApplication)
        .join(Job)
        .filter(Job.recruiter_id == recruiter.id)
        .all()
    )
    
    return [
        {
            "application_id": app.application_id,
            "job_title": app.job.title,
            "candidate_name": app.candidate.full_name,
            "status": app.status,
            "applied_at": app.applied_at
        }
        for app in applications
    ]

@router.get("/recruiter/applications/{job_id}")
def get_job_applications(
    job_id: int,
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    job = db.query(Job).filter(Job.job_id == job_id, Job.recruiter_id == recruiter.id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    applications = (
        db.query(
            JobApplication,
            User.full_name,
            Candidate.current_job_title,
            CandidateJobSuitability.suitability_score
        )
        .join(Candidate, JobApplication.candidate_id == Candidate.candidate_id)
        .join(User, Candidate.candidate_id == User.id)
        .outerjoin(
            CandidateJobSuitability,
            and_(
                CandidateJobSuitability.job_id == JobApplication.job_id,
                CandidateJobSuitability.candidate_id == JobApplication.candidate_id
            )
        )
        .filter(JobApplication.job_id == job_id)
        .all()
    )

    if not applications:
        # Return job details with an empty applications list if no applications are found
        return {
            "job_title": job.title,
            "job_location": job.location,
            "job_time": job.time,
            "job_company": job.company_name,
            "job_description": job.long_description,
            "applications": []
        }

    # Creating the response object
    response = {
        "job_title": job.title,
        "job_location": job.location,
        "job_time": job.time,
        "job_company": job.company_name,
        "job_description": job.long_description,
        "applications": [
            {
                "application_id": app.JobApplication.application_id,
                "candidate_name": app.full_name,
                "current_job_title": app.current_job_title,
                "suitability_score": app.suitability_score,
                "status": app.JobApplication.status,
                "applied_at": app.JobApplication.applied_at,
            }
            for app in applications
        ]
    }
    return response

@router.get("/recruiter/application/{application_id}")
def get_application_details(
    application_id: int,
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    # Get application with all related data
    application = (
        db.query(JobApplication)
        .join(Job)
        .filter(
            JobApplication.application_id == application_id,
            Job.recruiter_id == recruiter.id
        )
        .first()
    )
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get candidate details
    candidate = application.candidate
    candidate_details = db.query(Candidate).filter(Candidate.candidate_id == candidate.id).first()
    
    # Get resume
    resume = db.query(Resume).filter(Resume.user_id == candidate.id).first()

    return {
        "application_details": {
            "application_id": application.application_id,
            "status": application.status,
            "applied_at": application.applied_at,
            "final_result": application.final_result.value if application.final_result else "Pending",
            "feedback": application.feedback if hasattr(application, 'feedback') else None
        },
        "job_details": {
            "title": application.job.title,
            "company_name": application.job.company_name,
            "description": application.job.long_description
        },
        "candidate_details": {
            "name": candidate.full_name,
            "email": candidate.email,
            "current_job_title": candidate_details.current_job_title,
            "years_of_experience": candidate_details.years_of_experience,
            "highest_education": candidate_details.highest_education,
            "brief_intro": candidate_details.brief_intro
        },
        "resume_details": {
            "education": resume.education if resume else None,
            "experience": resume.experience if resume else None,
            "skills": resume.skills if resume else None,
            "certifications": resume.certifications if resume else None,
            "projects": resume.projects if resume else None,
            "achievements": resume.achievements if resume else None
        }
    }

@router.get("/recruiter/evaluations/{application_id}")
def get_application_evaluation(
    application_id: int,
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    """
    Returns the interview evaluation results for a specific application.
    Only accessible by the recruiter who posted the related job.
    """
    # Get the application and check if it exists
    application = db.query(JobApplication).filter(JobApplication.application_id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if the recruiter is authorized (owns the job)
    job = db.query(Job).filter(Job.job_id == application.job_id).first()
    if job.recruiter_id != recruiter.id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this evaluation")
    
    # Get the interview associated with this application
    interview = db.query(Interview).filter(
        Interview.job_id == application.job_id,
        Interview.candidate_id == application.candidate_id
    ).first()
    
    if not interview:
        return {
            "application_id": application_id,
            "status": application.status.value,
            "message": "No interview data available for this application",
            "has_interview": False,
            "has_evaluation": False
        }
    
    # Get the evaluation if it exists
    evaluation = db.query(InterviewEvaluation).filter(
        InterviewEvaluation.interview_id == interview.id
    ).first()
    
    if not evaluation:
        return {
            "application_id": application_id,
            "status": application.status.value,
            "message": "Interview completed but not yet evaluated",
            "has_interview": True,
            "has_evaluation": False,
            "interview_id": interview.id
        }
    
    # Get candidate details
    candidate = db.query(User).filter(User.id == application.candidate_id).first()
    
    # Return the complete evaluation data
    return {
        "application_id": application_id,
        "job_details": {
            "job_id": job.job_id,
            "title": job.title,
            "company_name": job.company_name
        },
        "candidate_details": {
            "candidate_id": candidate.id,
            "name": candidate.full_name,
            "email": candidate.email
        },
        "interview_details": {
            "interview_id": interview.id,
            "date_completed": interview.created_at,
            "conversation_log": interview.conversation_log,
            "tab_switch_count": interview.tab_switch_count,
            "face_violation_count": interview.face_violation_count
        },
        "evaluation": {
            "evaluation_id": evaluation.evaluation_id,
            "evaluation_score": evaluation.evaluation_score,
            "strengths": evaluation.strengths,
            "weaknesses": evaluation.weaknesses,
            "ai_feedback": evaluation.ai_feedback,
            "feedback_for_candidate": evaluation.feedback_for_candidate,
            "sentiment_analysis": evaluation.sentiment_analysis,
            "technical_knowledge": evaluation.technical_knowledge,
            "created_at": evaluation.created_at
        },
        "has_interview": True,
        "has_evaluation": True,
        "status": application.status
    }

@router.get("/recruiter/all-applications")
def get_all_applications_with_details(
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    applicants = (
        db.query(
            JobApplication,
            Job.title,
            Job.company_name,
            User.full_name,
            User.email,
            CandidateJobSuitability.suitability_score
        )
        .join(Job, JobApplication.job_id == Job.job_id)
        .join(Candidate, JobApplication.candidate_id == Candidate.candidate_id)
        .join(User, Candidate.candidate_id == User.id)
        .outerjoin(
            CandidateJobSuitability,
            and_(
                CandidateJobSuitability.job_id == JobApplication.job_id,
                CandidateJobSuitability.candidate_id == JobApplication.candidate_id
            )
        )
        .filter(Job.recruiter_id == recruiter.id)
        .all()
    )

    return [
        {
            "application_id": app.JobApplication.application_id,
            "job_title": app.title,
            "company_name": app.company_name,
            "candidate_name": app.full_name,
            "candidate_email": app.email,
            "application_status": app.JobApplication.status,
            "suitability_score": app.suitability_score,
            "applied_at": app.JobApplication.applied_at
        }
        for app in applicants
    ]

@router.post("/recruiter/application/{application_id}/final-result")
def submit_final_result(
    application_id: int,
    final_result: FinalResultRequest,
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    """
    Submit the final result (Accept/Reject) for a job application after interview.
    This should be called after the interview and evaluation process.
    """
    # Get the application
    application = db.query(JobApplication).filter(JobApplication.application_id == application_id).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if recruiter owns the job
    job = db.query(Job).filter(Job.job_id == application.job_id).first()
    if job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=403, 
            detail="You are not authorized to provide final results for this application"
        )
    
    # Check if the application has completed an interview
    if application.status != ApplicationStatus.INTERVIEW_COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail="Cannot provide final result until interview is completed"
        )
    
    # Update the application with the final result
    result_map = {
        "accepted": FinalResult.ACCEPTED,
        "rejected": FinalResult.REJECTED
    }
    
    if final_result.result.lower() not in result_map:
        raise HTTPException(
            status_code=400,
            detail="Result must be either 'accepted' or 'rejected'"
        )
    
    application.final_result = result_map[final_result.result.lower()]
    
    # Store feedback if provided
    if hasattr(application, 'feedback') and final_result.feedback:
        application.feedback = final_result.feedback
    elif final_result.feedback and not hasattr(application, 'feedback'):
        # If the model doesn't have a feedback column, log it but don't fail
        print(f"Feedback provided but no column exists: {final_result.feedback}")
    
    db.commit()
    
    # Send email notification to candidate (in real implementation)
    # await send_result_email(application.candidate.email, final_result.result, final_result.feedback)
    
    return {
        "status": "success",
        "message": f"Application {final_result.result} successfully",
        "application_id": application_id,
        "final_result": application.final_result.value
    }