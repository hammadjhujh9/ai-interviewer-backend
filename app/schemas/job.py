# schemas/job.py
from pydantic import BaseModel
from typing import Optional
import enum

class JobLocation(str, enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"

class JobTime(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"

class JobBase(BaseModel):
    title: str
    location: JobLocation
    time: JobTime
    short_description: str
    long_description: str
    requirements: str
    max_salary: Optional[float] = None
    min_salary: Optional[float] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[JobLocation] = None
    time: Optional[JobTime] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    requirements: Optional[str] = None
    max_salary: Optional[float] = None
    min_salary: Optional[float] = None

class JobResponse(JobBase):
    job_id: int
    company_name: str
    recruiter_id: int

    class Config:
        from_attributes = True
