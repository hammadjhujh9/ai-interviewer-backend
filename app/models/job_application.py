from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from enum import Enum as PyEnum

class ApplicationStatus(PyEnum):
    PENDING = "Pending"
    REVIEWED = "Reviewed"
    INTERVIEW_SCHEDULED = "Interview Scheduled"
    INTERVIEW_COMPLETED = "Interview Completed"
    REJECTED = "Rejected"

class FinalResult(PyEnum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"

class JobApplication(Base):
    __tablename__ = "job_applications"

    application_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.job_id"))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    applied_at = Column(DateTime, default=datetime.utcnow)
    final_result = Column(Enum(FinalResult), default=FinalResult.PENDING)
    
    candidate = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    interview = relationship("Interview", back_populates="application", uselist=False)


