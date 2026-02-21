# api/jobs.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Recruiter, User
from app.models.job import Job
from app.services.job import (
    create_job, get_jobs_by_recruiter, get_job_by_id, update_job, delete_job, get_all_jobs
)
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.api.auth import get_current_recruiter, get_current_candidate
from app.services.suitability import calculate_suitability, store_suitability_score
from app.models.suitability import CandidateJobSuitability
from app.models.job_application import JobApplication

router = APIRouter()


def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@router.post("/recruiter/jobs", response_model=JobResponse)
def post_job(job: JobCreate, db: Session = Depends(get_db), recruiter=Depends(get_current_recruiter)):
    recruiter_obj = db.query(Recruiter).filter(Recruiter.recruiter_id == recruiter.id).first()
    if not recruiter_obj:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    new_job = create_job(db, job, recruiter_id=recruiter.id, company_name=recruiter_obj.company_name)
    return new_job

@router.get("/recruiter/jobs", response_model=list[JobResponse])
def list_jobs(db: Session = Depends(get_db), recruiter=Depends(get_current_recruiter)):
    return get_jobs_by_recruiter(db, recruiter.id)

@router.get("/recruiter/jobs/{job_id}", response_model=JobResponse)
def retrieve_job(job_id: int, db: Session = Depends(get_db), recruiter=Depends(get_current_recruiter)):
    job = get_job_by_id(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/recruiter/jobs/{job_id}", response_model=JobResponse)
def modify_job(job_id: int, job_data: JobUpdate, db: Session = Depends(get_db), recruiter=Depends(get_current_recruiter)):
    updated_job = update_job(db, job_id, job_data, recruiter.id)
    if not updated_job:
        raise HTTPException(status_code=403, detail="Not allowed to update this job")
    return updated_job

@router.delete("/recruiter/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_job(job_id: int, db: Session = Depends(get_db), recruiter=Depends(get_current_recruiter)):
    deleted_job = delete_job(db, job_id, recruiter.id)
    if not deleted_job:
        raise HTTPException(status_code=403, detail="Not allowed to delete this job")

# Candidate Endpoints
@router.get("/candidate/jobs")
def get_jobs_for_candidate(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_candidate),
):
    # Fetch all jobs
    jobs = db.query(Job).all()

    # Fetch suitability scores for the current candidate
    job_suitability = (
        db.query(CandidateJobSuitability)
        .filter(CandidateJobSuitability.candidate_id == current_user.id)
        .all()
    )

    # Create a dictionary for quick lookup of suitability scores
    job_suitability_dict = {js.job_id: js.suitability_score for js in job_suitability}

    # Fetch jobs the candidate has applied for
    applied_jobs = (
        db.query(Job)
        .join(Job.applications)
        .filter(Job.applications.any(candidate_id=current_user.id))
        .all()
    )
    applied_job_ids = {job.job_id for job in applied_jobs}

    # For jobs that don't have a suitability score, calculate it
    for job in jobs:
        if job.job_id not in job_suitability_dict:
            # Calculate the suitability score using LLM
            suitability_score = calculate_suitability(db, current_user, job)

            candidateJobSuitability = store_suitability_score(db, current_user, job, suitability_score)

            job_suitability_dict[job.job_id] = suitability_score

    # Create a list of jobs with their suitability scores and application status
    jobs_with_scores = []
    for job in jobs:
        job_dict = {
            "job_id": job.job_id,
            "title": job.title,
            "company_name": job.company_name,
            "location": job.location,
            "time": job.time,
            "short_description": job.short_description,
            "long_description": job.long_description,
            "requirements": job.requirements,
            "max_salary": job.max_salary,
            "min_salary": job.min_salary,
            "created_at": job.created_at,
            "suitability_score": job_suitability_dict.get(job.job_id, 0),
            "recruiter_id": job.recruiter_id,
            "has_applied": job.job_id in applied_job_ids,
        }
        jobs_with_scores.append(job_dict)
    
    return jobs_with_scores

@router.get("/candidate/jobs/{job_id}")
def get_job_details_for_candidate(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_candidate),
):
    """
    Get details of a specific job for a candidate including suitability score
    and application status.
    """
    # Fetch the specific job
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if the candidate has already applied for this job
    has_applied = db.query(JobApplication).filter(
        JobApplication.candidate_id == current_user.id,
        JobApplication.job_id == job_id
    ).first() is not None
    
    # Get suitability score for this job
    suitability = db.query(CandidateJobSuitability).filter(
        CandidateJobSuitability.candidate_id == current_user.id,
        CandidateJobSuitability.job_id == job_id
    ).first()
    
    # If no suitability score exists, calculate it
    suitability_score = 0
    if not suitability:
        suitability_score = calculate_suitability(db, current_user, job)
        store_suitability_score(db, current_user, job, suitability_score)
    else:
        suitability_score = suitability.suitability_score
    
    # Create response with job details and candidate-specific information
    job_details = {
        "job_id": job.job_id,
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "time": job.time,
        "short_description": job.short_description,
        "long_description": job.long_description,
        "requirements": job.requirements,
        "max_salary": job.max_salary,
        "min_salary": job.min_salary,
        "created_at": job.created_at,
        "suitability_score": suitability_score,
        "recruiter_id": job.recruiter_id,
        "has_applied": has_applied,
    }
    
    return job_details
