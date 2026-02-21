# app/services/suitability.py

from app.models.resume import Resume
from app.models.suitability import CandidateJobSuitability
from app.models.job import Job
from app.models.user import Candidate, User
from sqlalchemy.orm import Session
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv(".env", override=True)

def calculate_suitability(db: Session, current_user: User, job: Job) -> float:
    """Calculates suitability score using Groq API and LLaMA model."""
    # Fetch the candidate's resume from the database
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        return 0  # Return 0 if no resume is found

    # Initialize Groq API client
    client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

    # Prepare the structured prompt
    prompt = f"""
        Evaluate how well the following candidate's resume matches the job description provided.
        Assign a suitability score from 0 to 100 based on how closely the resume aligns with the job requirements.

        **Candidate Resume:**
        - Name: {resume.name}
        - Contact: {resume.contact}
        - Education: {resume.education}
        - Experience: {resume.experience}
        - Skills: {resume.skills}
        - Certifications: {resume.certifications}
        - Languages: {resume.languages}
        - Projects: {resume.projects}
        - Achievements: {resume.achievements}

        **Job Details:**
        - Title: {job.title}
        - Requirements: {job.requirements}
        - Short Description: {job.short_description}
        - Long Description: {job.long_description}

        Please provide a suitability score as a JSON response with the following format:
        {{"suitability_score": <score>}}
    """

    # Call the Groq API
    try:
        completion = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            # max_tokens=1024,
            top_p=1,
            stream=False,
            response_format={ "type": "json_object" }
        )
        result = completion.choices[0].message.content.strip()
        print(f"Groq API response for calculate_suitability: {result}")

        # Extract and parse the result
        import json
        parsed_result = json.loads(result)
        return parsed_result.get("suitability_score", 0)
    
    except Exception as e:
        print(f"Error connecting to Groq API: {e}")
        return 0

# def store_suitability_score(db: Session, candidate: User, job: Job, suitability_score: float):
#     suitability = CandidateJobSuitability(
#         candidate_id=candidate.id,
#         job_id=job.job_id,
#         suitability_score=suitability_score
#     )
#     db.add(suitability)
#     db.commit()
#     db.refresh(suitability)
#     return suitability

def store_suitability_score(db: Session, candidate: User, job: Job, suitability_score: float):
    # Try to find existing suitability record
    suitability = db.query(CandidateJobSuitability).filter(
        CandidateJobSuitability.candidate_id == candidate.id,
        CandidateJobSuitability.job_id == job.job_id
    ).first()

    if suitability:
        # Explicitly update the score
        print(f"Updating suitability score for candidate {candidate.id} and job {job.job_id}")
        suitability.suitability_score = suitability_score
        db.merge(suitability)  # Use merge to ensure update
        db.commit()
    else:
        # Create new suitability score
        print(f"Creating new suitability score for candidate {candidate.id} and job {job.job_id}")
        suitability = CandidateJobSuitability(
            candidate_id=candidate.id, 
            job_id=job.job_id, 
            suitability_score=suitability_score
        )
        db.add(suitability)
        db.commit()

    db.refresh(suitability)
    return suitability