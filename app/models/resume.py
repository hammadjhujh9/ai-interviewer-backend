from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import JSON

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    contact = Column(JSON)
    education = Column(JSON)
    experience = Column(JSON)
    skills = Column(JSON)
    certifications = Column(JSON)
    languages = Column(JSON)
    projects = Column(JSON)
    achievements = Column(JSON)
    
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="resume")
