# app/models/suitability.py

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.job import Job
from app.models.user import User

class CandidateJobSuitability(Base):
    __tablename__ = "candidate_job_suitability"
    
    id = Column(Integer, primary_key=True, index=True)
    suitability_score = Column(Float)  # Suitability score as a float (0.0 to 100.0)
    
    candidate_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.job_id"))
    
    candidate = relationship("User", back_populates="suitability_scores")
    job = relationship("Job", back_populates="suitability_scores")

