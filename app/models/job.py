# models/job.py
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text, DateTime,Float
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

class JobLocation(enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"

class JobTime(enum.Enum):
    full_time = "full_time"
    part_time = "part_time"

class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    location = Column(Enum(JobLocation), nullable=False)
    time = Column(Enum(JobTime), nullable=False)
    short_description = Column(String, nullable=False)
    long_description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    max_salary = Column(Float, nullable=True)
    min_salary = Column(Float, nullable=True)

    recruiter = relationship("User", back_populates="jobs")
    suitability_scores = relationship("CandidateJobSuitability", back_populates="job")
    applications = relationship("JobApplication", back_populates="job")
    interviews = relationship("Interview", back_populates="job")

