from pydantic import BaseModel, RootModel
from typing import List, Optional, Union, Any


class ContactInfo(BaseModel):
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None


class Education(BaseModel):
    degree: str
    institution: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Experience(BaseModel):
    job_title: str
    company: str
    start_date: str
    end_date: str
    responsibilities: Optional[str] = None


class Certification(BaseModel):
    title: str
    issuer: Optional[str] = None
    date: Optional[str] = None


class Language(BaseModel):
    language: str
    proficiency: Optional[str] = None


class Project(BaseModel):
    project_title: str
    description: str
    technologies: Optional[Union[str, List[str]]] = None


class ResumeResponse(BaseModel):
    name: str
    contact: Optional[ContactInfo] = None
    education: Optional[List[Education]] = None
    experience: Optional[List[Experience]] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[Certification]] = None
    languages: Optional[List[Language]] = None
    projects: Optional[List[Project]] = None
    achievements: Optional[List[str]] = None

class ResumeResponseWithFallback(RootModel):
    root: Union[ResumeResponse, bool]