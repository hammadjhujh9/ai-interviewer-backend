from sqlalchemy.orm import Session
from app.models.job_application import JobApplication, ApplicationStatus
from app.models.job import Job
from app.models.user import User
from app.services.email import send_interview_email

def create_application(db: Session, candidate_id: int, job_id: int) -> JobApplication:
    job_application = JobApplication(candidate_id=candidate_id, job_id=job_id)
    db.add(job_application)
    db.commit()
    db.refresh(job_application)
    return job_application

async def schedule_interview(candidate: User, job: Job,application_id:int, db: Session):
    # interview_link = f"https://interview.recruiter.ai/{application_id}"
    # interview_link = f"https://interview.recruiter.ai/{application_id}"
    interview_link = f"http://127.0.0.1:3000/interview/{application_id}"
    await send_interview_email(candidate.email, job.title, interview_link)
    return interview_link
