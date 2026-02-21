# app/schemas/user.py
from pydantic import BaseModel
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    candidate = "candidate"
    recruiter = "recruiter"

class UserBase(BaseModel):
    email: str
    full_name: str
    password: str

class CandidateCreate(UserBase):
    role: UserRole = UserRole.candidate
    current_job_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    highest_education: Optional[str] = None
    brief_intro: Optional[str] = None

class RecruiterCreate(UserBase):
    role: UserRole = UserRole.recruiter
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    company_summary: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
