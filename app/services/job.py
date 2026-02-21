# services/job.py
from sqlalchemy.orm import Session
from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate

def create_job(db: Session, job_data: JobCreate, recruiter_id: int, company_name: str):
    job = Job(**job_data.dict(), recruiter_id=recruiter_id, company_name=company_name)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_jobs_by_recruiter(db: Session, recruiter_id: int):
    return db.query(Job).filter(Job.recruiter_id == recruiter_id).all()

def get_job_by_id(db: Session, job_id: int, recruiter_id: int):
    return db.query(Job).filter(Job.job_id == job_id, Job.recruiter_id == recruiter_id).first()

def update_job(db: Session, job_id: int, job_data: JobUpdate, recruiter_id: int):
    job = get_job_by_id(db, job_id, recruiter_id)
    if job:
        if job.recruiter_id != recruiter_id:
            return None  # Recruiter is not allowed to update this job
        for key, value in job_data.dict(exclude_unset=True).items():
            setattr(job, key, value)
        db.commit()
        db.refresh(job)
    return job

def delete_job(db: Session, job_id: int, recruiter_id: int):
    job = get_job_by_id(db, job_id, recruiter_id)
    if job:
        if job.recruiter_id != recruiter_id:
            return None  # Recruiter is not allowed to delete this job
        db.delete(job)
        db.commit()
    return job

def get_all_jobs(db: Session):
    # Retrieve all job postings from the database
    jobs = db.query(Job).all()
    return jobs