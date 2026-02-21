import json
from groq import Groq
from sqlalchemy.orm import Session
from app.models.interview import Interview
from app.models.interview_evaluation import InterviewEvaluation
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import Candidate
from app.services.email import send_evaluation_report_email

# Initialize Groq Client
client = Groq()

async def evaluate_interview(db: Session, interview_id: int):
    """Fetch interview data, candidate info, job description, resume data, evaluate using LLM, and store the results."""
    
    # Fetch interview and related data
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    
    if not interview:
        return {"error": "Interview not found"}

    # Fetch job details
    job = db.query(Job).filter(Job.job_id == interview.job_id).first()
    if not job:
        return {"error": "Associated job not found"}

    # Fetch candidate details
    candidate = db.query(Candidate).filter(Candidate.candidate_id == interview.candidate_id).first()
    if not candidate:
        return {"error": "Candidate not found"}
    
    # Fetch candidate resume
    resume = db.query(Resume).filter(Resume.user_id == interview.candidate_id).first()
    
    # Prepare structured data
    interview_data = {
        "job_title": job.title,
        "job_description": job.long_description,
        "job_company": job.company_name,
        "job_requirements": job.requirements,
        "job_location": job.location,
        "job_time": job.time,
        "candidate_name": resume.name if resume else None,
        "candidate_contact": resume.contact if resume else None,
        "candidate_education": resume.education if resume else None,
        "candidate_experience": resume.experience if resume else None,
        "candidate_skills": resume.skills if resume else None,
        "candidate_certifications": resume.certifications if resume else None,
        "candidate_languages": resume.languages if resume else None,
        "candidate_projects": resume.projects if resume else None,
        "candidate_achievements": resume.achievements if resume else None,
        "interview_conversation_log": interview.conversation_log,  # Assuming this is stored as JSON
        "tab_switch_count": interview.tab_switch_count or 0,
        "face_violation_count": interview.face_violation_count or 0
    }
    
    system_prompt = """
    You are an expert recruiter tasked with evaluating a candidate’s performance in a job interview based on the provided job details, candidate information, and interview conversation log. Please follow these guidelines to produce a comprehensive and fair evaluation:

    ### Evaluation Criteria:
    - **Score (0-100)**: Assign a numerical score based on the following:
    - **Relevance**: How effectively the candidate’s responses address the questions and align with the job requirements.
    - **Clarity**: The coherence, articulateness, and structure of the candidate’s answers.
    - **Job Fit**: How well the candidate’s skills, experience, and responses align with the role’s needs.
    - **Proctoring Impact**: Deduct 5–10 points for significant proctoring issues (e.g., >5 tab switches or >3 face violations), reflecting lack of focus or professionalism.
    - **Strengths**: Highlight specific strengths in the candidate’s performance, such as technical expertise, communication skills, or relevant experience.
    
    - **Weaknesses**: Identify areas where the candidate could improve, such as gaps in knowledge, unclear answers, or missing details.

    - **Sentiment Analysis**: Analyze the sentiment of the candidate’s responses in the conversation log (e.g., Positive, Neutral, Negative). Focus on tone, confidence, and emotional cues like hesitation. Provide a brief explanation (1-2 sentences).

    - **Technical Knowledge**: Assess the candidate’s technical expertise as demonstrated in the conversation log, job requirements, and resume. Rate as Strong, Moderate, or Weak, and provide a brief explanation (1-2 sentences).

    - **AI Feedback**: Provide constructive feedback on the candidate’s overall performance (100-200 words). Reference specific responses and job requirements in your analysis.

    - **Feedback for Candidate**: Offer personalized, actionable suggestions (100-200 words) to help the candidate improve. Write in a supportive and professional tone.

    ### Guidelines:
    1. **Relevance**:
    - Ensure the evaluation is based on the job’s requirements and the candidate’s qualifications.
    - Focus on how well the candidate’s responses reflect their suitability for the role.
    - Compare all of the candidate's responses to check if there is a contradiction in the candidate's responses, if there is a contradiction, then the candidate's response should be marked as Weak and highlight the contradiction in the feedback for the candidate.
    
    2. **Fairness**:
    - Evaluate based solely on the provided data, avoiding assumptions or biases.
    - Consider the candidate’s experience level and the context of their responses.
    - Answer if not answered accurately or if candidate's response only has "thank you", it means the candidate is not able to answer the question.
    - Marking and scoring should be based on the candidate's answer's quality and how well it matches the job requirements, no leniency required.
    - Grading should be strict, do not grade the candidate's response's if it is not relevant to the job requirements.
    - If the candidate answers fewer than 7 substantial technical questions, apply a minimum 20-point deduction, even if some answers are good. If the candidate answers fewer than 5 technical questions, cap the total score at 50.
    - Disregard generic, irrelevant, or placeholder responses (e.g., “thank you”, “I’m not sure”) when counting valid answers.

    3. **Proctoring**:
    - Consider tab switches and face violations as indicators of focus and professionalism.
    - Significant issues (e.g., >5 tab switches or >3 face violations) should lower the score by 5–10 points and be noted in weaknesses and feedback.    
    - If the candidate has more than 5 tab switches or more than 3 face violations, then mark the candidate's response as Weak and highlight the proctoring issues in the feedback for the candidate.
    
    4. **Clarity and Tone**:
    - Use professional, neutral language that’s suitable for a recruitment context.
    - Provide specific feedback, citing examples from the conversation log where applicable.

    5. **Output Format**:
    - Return the evaluation as a JSON object with the following structure:
        ```json
        {
        "evaluation_score": 85.5,
        "strengths": "Clear communication, strong problem-solving.",
        "weaknesses": "Needs deeper technical explanations.",
        "sentiment_analysis": {
            "sentiment": "Positive",
            "explanation": "The candidate was confident and enthusiastic, reflecting strong engagement."
        },
        "technical_knowledge": {
            "rating": "Strong",
            "explanation": "Demonstrated solid expertise in Django through detailed project descriptions."
        },
        "ai_feedback": "The candidate demonstrated strong communication but should provide more in-depth technical explanations.",
        "feedback_for_candidate": "Great job! Focus on providing more detailed technical explanations to demonstrate expertise."
        }
        ```
    - Ensure all fields are present. Feedback fields should meet the 100-200 word requirement. Sentiment and technical knowledge explanations should be concise (1-2 sentences).
    - Do not include additional text or formatting outside the JSON object.

    **Input**: The user will provide job details, candidate information, and the interview conversation log. Use this data to generate the evaluation.
    """

    user_prompt = f"""
    ### Job Details:
    - **Job Title**: {interview_data['job_title']}
    - **Job Description**: {interview_data['job_description']}
    - **Job Requirements**: {interview_data['job_requirements']}
    - **Company**: {interview_data['job_company']}
    - **Location**: {interview_data['job_location']}
    - **Time**: {interview_data['job_time']}

    ### Candidate Details:
    - **Name**: {interview_data['candidate_name']}
    - **Experience**: {interview_data['candidate_experience']}
    - **Education**: {interview_data['candidate_education']}
    - **Skills**: {interview_data['candidate_skills']}
    - **Certifications**: {interview_data['candidate_certifications']}
    - **Languages**: {interview_data['candidate_languages']}
    - **Projects**: {interview_data['candidate_projects']}
    - **Achievements**: {interview_data['candidate_achievements']}

    ### Interview Conduct Metrics:
    - **Tab Switch Count**: {interview_data['tab_switch_count']} (Number of times candidate switched to another tab/window during interview)
    - **Face Violation Count**: {interview_data['face_violation_count']} (Number of times candidate's face was not detected during interview)

    ### Interview Conversation Log:
    ```json
    {json.dumps(interview_data['interview_conversation_log'], indent=2)}
    ```
        """
    
    # Send request to Groq LLM
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
                ],
        temperature=0.6,
        top_p=0.95,
        response_format={"type": "json_object"},
        stream=False
    )

    # Extract response content
    ai_response = response.choices[0].message.content

    try:
        # Parse AI JSON response
        evaluation_data = json.loads(ai_response)
    except Exception as e:
        return {"error": f"Failed to parse AI response: {str(e)}"}

    # Save evaluation to DB
    interview_evaluation = InterviewEvaluation(
        interview_id=interview_id,
        evaluation_score=evaluation_data["evaluation_score"],
        strengths=evaluation_data["strengths"],
        weaknesses=evaluation_data["weaknesses"],
        ai_feedback=evaluation_data["ai_feedback"],
        feedback_for_candidate=evaluation_data["feedback_for_candidate"],
        sentiment_analysis=evaluation_data["sentiment_analysis"],
        technical_knowledge=evaluation_data["technical_knowledge"]
    )
    
    db.add(interview_evaluation)
    db.commit()
    db.refresh(interview_evaluation)

    # Add violation counts to the evaluation data for the email
    evaluation_data_with_violations = evaluation_data.copy()
    evaluation_data_with_violations["violations"] = {
        "tab_switch_count": interview.tab_switch_count or 0,
        "face_violation_count": interview.face_violation_count or 0
    }

    # Send evaluation report to candidate with violation counts
    await send_evaluation_report_email(
        candidate.user.email, 
        candidate.user.full_name, 
        job.title, 
        evaluation_data_with_violations
    )

    return evaluation_data["feedback_for_candidate"]
