from typing import Union
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.resume import parse_resume
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse, ResumeResponseWithFallback
from app.database import get_db
from app.api.auth import get_current_candidate
from app.services.suitability import calculate_suitability, store_suitability_score
from app.models.job import Job
from app.models.suitability import CandidateJobSuitability

router = APIRouter()

@router.post("/upload-resume", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_candidate)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        # Parse the resume and save it to the database
        new_resume = await parse_resume(file, db, current_user.id)
        # print(new_resume)
        # Fetch all jobs
        jobs = db.query(Job).all()
        # print(jobs)
        # Calculate suitability scores for each job
        for job in jobs:
            print('inside loop')
            suitability_score = calculate_suitability(db, current_user, job)
            print('suitability score inside loop',suitability_score)
            store_suitability_score(db, current_user, job, suitability_score)

        return new_resume

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")


@router.get("/resume", response_model=ResumeResponseWithFallback, status_code=status.HTTP_200_OK)
def get_resume(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_candidate)
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    
    if not resume:
        return False
    
    return resume 
