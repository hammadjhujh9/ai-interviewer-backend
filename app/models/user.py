# app/models/user.py
from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from app.database import Base
import uuid
from enum import Enum as PyEnum

class UserRole(PyEnum):
    candidate = "candidate"
    recruiter = "recruiter"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.candidate)
    created_at = Column(Integer)
    

class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    current_job_title = Column(String)
    years_of_experience = Column(Integer)
    highest_education = Column(String)
    brief_intro = Column(String)
    user = relationship("User", back_populates="candidate")

class Recruiter(Base):
    __tablename__ = "recruiters"

    recruiter_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    company_name = Column(String)
    job_title = Column(String)
    industry = Column(String)
    company_summary = Column(String)

    user = relationship("User", back_populates="recruiter")

User.candidate = relationship("Candidate", uselist=False, back_populates="user")
User.recruiter = relationship("Recruiter", uselist=False, back_populates="user")
    # Add this relationship for jobs
User.jobs = relationship("Job", back_populates="recruiter")
User.suitability_scores = relationship("CandidateJobSuitability", back_populates="candidate")
User.resume = relationship("Resume", back_populates="user", uselist=False)
User.applications = relationship("JobApplication", back_populates="candidate")
User.interviews = relationship("Interview", back_populates="candidate")