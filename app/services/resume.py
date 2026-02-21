from fastapi import HTTPException
from groq import Groq
import io
from PyPDF2 import PdfReader
from app.models.resume import Resume
from sqlalchemy.orm import Session
import json
import os
from dotenv import load_dotenv

load_dotenv(".env", override=True)

async def parse_resume(file: str, db: Session, user_id: int) -> Resume:
    try:
        # Extract text from the uploaded PDF
        pdf = PdfReader(io.BytesIO(await file.read()))
        text = "\n".join([page.extract_text() for page in pdf.pages])

        # Call Groq API for parsing
        client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
            )
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                        Please parse the following resume and extract the key details in a structured JSON format.Make sure json is a valid JSON. 
                        The JSON should contain the following fields:
                        {{
                        "name": "Full name of the candidate",
                        "contact": {{
                            "email": "Email address",
                            "phone": "Phone number",
                            "address": "Physical address"
                        }},
                        "education": [
                            {{
                            "degree": "Degree obtained",
                            "institution": "Name of the institution",
                            "start_date": "Start date of study",
                            "end_date": "End date of study (or 'Present' if currently studying)"
                            }}
                        ],
                        "experience": [
                            {{
                            "job_title": "Job title",
                            "company": "Company name",
                            "start_date": "Start date of employment",
                            "end_date": "End date of employment (or 'Present' if currently employed)",
                            "responsibilities": "Brief description of job responsibilities"
                            }}
                        ],
                        "skills": [
                            "List of skills the candidate possesses"
                        ],
                        "certifications": [
                            {{
                            "title": "Certification title",
                            "issuer": "Certification issuing body",
                            "date": "Date of certification"
                            }}
                        ],
                        "languages": [
                            {{
                            "language": "Language",
                            "proficiency": "Proficiency level (e.g., Beginner, Intermediate, Fluent)"
                            }}
                        ],
                        "projects": [
                            {{
                            "project_title": "Title of the project",
                            "description": "Brief description of the project",
                            "technologies": "List of technologies used"
                            }}
                        ],
                        "achievements": [
                            "List of notable achievements or awards"
                        ]
                        }}
                        The resume content to parse is:
                        {text}
                    """
                }
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
            response_format={"type": "json_object"}
        )

        # Extract parsed data
        parsed_data = completion.choices[0].message.content.strip()
        resume_data = json.loads(parsed_data)

        # print("Groq API Response:", resume_data)

        # Save the resume data in the database
        new_resume = Resume(
            name=resume_data.get("name", ""),
            contact=resume_data.get("contact", {}),
            education=resume_data.get("education", []),
            experience=resume_data.get("experience", []),
            skills=resume_data.get("skills", []),
            certifications=resume_data.get("certifications", []),
            languages=resume_data.get("languages", []),
            projects=resume_data.get("projects", []),
            achievements=resume_data.get("achievements", []),
            user_id=user_id
        )

        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)

        return new_resume

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")
