from sqlalchemy import Column, DateTime, Integer, ForeignKey, String, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.application_id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.job_id"), nullable=False)  # Fix job_id reference
    conversation_log = Column(JSON, default=list)  # Store the conversation log as a JSON object
    status = Column(String, default="ongoing")  # "ongoing", "completed", etc.
    created_at = Column(DateTime, default=datetime.utcnow)  # Add timestamp

    tab_switch_count = Column(Integer, default=0)
    face_violation_count = Column(Integer, default=0)


    candidate = relationship("User", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    application = relationship("JobApplication", back_populates="interview")
    evaluations = relationship("InterviewEvaluation", back_populates="interview", cascade="all, delete")

