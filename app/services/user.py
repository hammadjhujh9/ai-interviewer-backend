# app/services/user.py
from sqlalchemy.orm import Session
from app.models.user import User, Candidate, Recruiter, UserRole
from app.schemas.user import CandidateCreate, RecruiterCreate
from passlib.context import CryptContext
from typing import Union

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: Union[CandidateCreate, RecruiterCreate]):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        email=user.email, 
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create the related Candidate or Recruiter record
    if user.role.value == UserRole.candidate.value:
        db_candidate = Candidate(
            candidate_id=db_user.id,
            current_job_title=user.current_job_title,
            years_of_experience=user.years_of_experience,
            highest_education=user.highest_education,
            brief_intro=user.brief_intro
        )
        db.add(db_candidate)
    elif user.role.value == UserRole.recruiter.value:
        db_recruiter = Recruiter(
            recruiter_id=db_user.id,
            company_name=user.company_name,
            job_title=user.job_title,
            industry=user.industry,
            company_summary=user.company_summary
        )
        db.add(db_recruiter)


    db.commit()
    print(f"Committed to database")  # Debug statement
    return db_user