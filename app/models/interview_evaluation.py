from sqlalchemy import Column, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class InterviewEvaluation(Base):
    __tablename__ = "interview_evaluations"

    evaluation_id = Column(Integer, primary_key=True, index=True)  # Changed to Integer to match Interview
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)  # Changed to match Interview.id
    evaluation_score = Column(Float, nullable=False)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    feedback_for_candidate = Column(Text, nullable=True)  # New field for candidate feedback
    
    # New fields to store sentiment analysis and technical knowledge as JSON
    sentiment_analysis = Column(JSON, nullable=True)
    technical_knowledge = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with the Interview model
    interview = relationship("Interview", back_populates="evaluations")
    
