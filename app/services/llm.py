import os
from typing import List
from groq import Groq

from app.models.job import Job
from app.models.resume import Resume

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.temperature = 0.5
        self.max_tokens = 4096
        self.top_p = 0.6

    def generate_follow_up_question(self, response_text: str, conversation_history: list) -> str:
        """
        Generate a follow-up question based on the candidate's response and conversation history.
        """
        prompt = f"""
        The candidate just said: "{response_text}"
        Conversation so far: {conversation_history}

        Provide a single follow-up question directly related to the last response. 
        Only return the question in plain text. 
        """
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stream=True,
                stop=None,
            )

            # Aggregate the response from the streamed chunks
            follow_up_question = ""
            for chunk in completion:
                follow_up_question += chunk.choices[0].delta.content or ""
            
            return follow_up_question.strip()
        except Exception as e:
            print(f"Error generating follow-up question: {e}")
            return None

    def generate_next_question(self, response_text: str, conversation_history: list, question_pool: list,job:Job,resume:Resume) -> str:
        """
        Generate the next question based on the conversation history and available questions.
        """

        job_details={
            "title": job.title,
            "company_name": job.company_name,
            "location": job.location,
            "short_description": job.short_description,
            "long_description": job.long_description,
            "requirements": job.requirements
        }
        resume_details = {
            "name": resume.name,
            "contact": resume.contact,
            "education": resume.education,
            "experience": resume.experience,
            "skills": resume.skills,
            "certifications": resume.certifications,
            "languages": resume.languages,
            "projects": resume.projects,
            "achievements": resume.achievements
        }

        system_prompt = f"""
        You are an expert interviewer conducting a real-time, professional interview for a specific job role. Your goal is to guide the conversation dynamically, selecting or generating the most relevant question based on the job details, candidate’s resume, conversation history, latest response, and available question pool. Follow these guidelines:

        ### Job Details:
        {job_details}

        ### Candidate's Resume:
        {resume_details}

        ### Available Questions:
        {question_pool}

        ### Guidelines:

        1. **Starting the Interview**:
        - If the conversation history is empty, begin with a welcoming, open-ended question to make the candidate feel comfortable. For example, ask them to introduce themselves or share relevant background information related to the role.
        - If the candidate's response is only "thank you", then ask a follow-up question to make the conversation more engaging.


        2. **Dynamic Question Selection**:
        - If the candidate’s latest response offers new insights or areas for exploration, generate a follow-up question to dive deeper into those points.
        - If no follow-up is necessary, choose a question from the available question pool or craft a new one that is aligned with the job requirements, candidate’s qualifications, or the natural flow of the conversation.

        3. **Relevance and Focus**:
        - Prioritize questions that assess the key skills, experiences, and qualities relevant to the role, as outlined in the job details and the candidate’s resume.
        - Focus on questions that advance the interview and help evaluate the candidate’s fit for the position.
        - Add fundamental questions maybe 2-3 to the question pool to make the interview more comprehensive (e.g. Questions from OOP, Data Structures, Database, etc.).

        4. **Conversation Management**:
        - Keep the interview on track by referencing past responses to avoid repetition, unless clarification is required.
        - Adjust your tone and questioning style based on the candidate’s responses, ensuring the conversation feels natural and engaging.

        5. **Tone and Clarity**:
        - Maintain a professional, neutral tone throughout the interview.
        - Formulate questions that are clear, concise, and encourage thoughtful, detailed responses.

        6. **Output**:
        - Return only the generated or selected question as plain text.
        - Do not include explanations, formatting, or extra context in your response.

        **Input**: The user will provide conversation history and the candidate’s latest response. Use these, along with the job details, resume, and question pool provided above, to generate the next question for the interview.
        """



        user_prompt = f"""
        ### Conversation History (so far):
        {conversation_history}

        ### Candidate's Latest Response:
        "{response_text}"
        """

    
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
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
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stream=True,
                stop=None,
            )

            question = ""
            for chunk in completion:
                question += chunk.choices[0].delta.content or ""
            
            return question.strip()
        except Exception as e:
            print(f"Error generating question: {e}")
            return None

    def generate_questions_pool(self, job: Job, resume: Resume) -> List[str]:

        job_details={
            "title": job.title,
            "company_name": job.company_name,
            "location": job.location,
            "short_description": job.short_description,
            "long_description": job.long_description,
            "requirements": job.requirements
        }

        resume_details = {
            "name": resume.name,
            "contact": resume.contact,
            "education": resume.education,
            "experience": resume.experience,
            "skills": resume.skills,
            "certifications": resume.certifications,
            "languages": resume.languages,
            "projects": resume.projects,
            "achievements": resume.achievements
        }

        system_prompt = """
        You are an expert in generating interview questions for job roles. Your task is to create a list of interview questions based on the provided job details and candidate resume. Follow these guidelines to ensure high-quality, relevant questions:

        1. **Question Focus**:
        - Generate questions that assess the candidate’s skills, qualifications, and suitability for the role.
        - Ensure questions align with the job requirements and the candidate’s experience as described in the resume.
        - Avoid using question that require typing as it is a verbal interview
        - The questions should be unique and not repetitive.

        2. **Question Types**:
        - Include a mix of:
            - **Technical questions**: To evaluate job-specific skills and knowledge.
            - **Behavioral questions**: To assess past experiences, soft skills, and cultural fit.
            - **Situational questions**: To gauge problem-solving and decision-making in hypothetical scenarios.

        3. **Relevance and Depth**:
        - Tailor questions to the role’s core responsibilities and the candidate’s background.
        - Avoid generic or overly broad questions; prioritize specificity to elicit detailed responses.

        4. **Quantity and Variety**:
        - Generate 5–10 questions, balancing the mix of technical, behavioral, and situational types.
        - Ensure no redundancy; each question should explore a unique aspect of the candidate’s fit.

        5. **Tone and Clarity**:
        - Use a professional, neutral tone suitable for a job interview.
        - Formulate clear, concise questions that encourage thoughtful, detailed answers.

        6. **Output Format**:
        - Return the questions as a plain bullet-point list, one question per bullet.
        - Do not include explanations, headings, or extra context in the output.

        **Input**: The user will provide the job details and candidate resume. Use this information to generate the interview questions.
        """
        user_prompt = f"""
        ### Job Details:
        {job_details}

        ### Resume:
        {resume_details}
        """
        
        completion = self.client.chat.completions.create(
            model=self.model,
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
            temperature=0.8,
            max_tokens=4096,
            top_p=1,
            stream=False,
            stop=None,
        )

        # Extract parsed data
        questions = completion.choices[0].message.content.strip()
        print("Generated questions:",questions.split("\n"))
        return questions.split("\n")
    
    def generate_first_question(self, question_pool: list,job: Job, resume: Resume) -> str:
        """
        Select the most appropriate first question from the question pool to start the interview.
        """
        job_details={
            "title": job.title,
            "company_name": job.company_name,
            "location": job.location,
            "short_description": job.short_description,
            "long_description": job.long_description,
            "requirements": job.requirements
        }
        resume_details = {
            "name": resume.name,
            "contact": resume.contact,
            "education": resume.education,
            "experience": resume.experience,
            "skills": resume.skills,
            "certifications": resume.certifications,
            "languages": resume.languages,
            "projects": resume.projects,
            "achievements": resume.achievements
        }
        prompt = f"""
        You are conducting an interview for the following role. Based on the provided question pool, job details, and candidate's resume, select the best possible opening question to begin the interview. Focus on a question that sets the tone, assesses the candidate's alignment with the role, or evaluates their most relevant skills or experiences.

        ### Job Details:
        {job_details}

        ### Candidate's Resume:
        {resume_details}

        ### Available Questions:
        {question_pool}

        Return only the selected question in plain text with no additional explanations or formatting.
        """

        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stream=True,
                stop=None,
            )

            question = ""
            for chunk in completion:
                question += chunk.choices[0].delta.content or ""
            
            return question.strip()
        except Exception as e:
            print(f"Error generating first question: {e}")
            return None
