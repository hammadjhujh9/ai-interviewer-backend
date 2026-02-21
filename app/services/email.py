from fastapi_mail import FastMail, MessageSchema
from app.config import mail_config


async def send_interview_email(email: str, job_title: str, interview_link: str):
    html_content = f"""
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
            body {{
                font-family: 'Inter', sans-serif;
                background-color: #111827;
                margin: 0;
                padding: 0;
                color: #e5e7eb;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: #1f2937;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                text-align: center;
            }}
            .header {{
                font-size: 22px;
                font-weight: 600;
                color: #f9fafb;
                margin-bottom: 20px;
            }}
            .content {{
                font-size: 16px;
                line-height: 1.6;
                color: #d1d5db;
                margin-bottom: 25px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 600;
                color: #ffffff;
                background-color: #2563eb;
                text-decoration: none;
                border-radius: 6px;
                transition: background 0.3s ease-in-out, transform 0.2s ease;
            }}
            .button:hover {{
                background-color: #1e40af;
                transform: scale(1.05);
            }}
            .divider {{
                height: 1px;
                background: #374151;
                margin: 25px 0;
            }}
            .footer {{
                font-size: 14px;
                color: #9ca3af;
                margin-top: 20px;
            }}
            .logo {{
                width: 80px;
                margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">You're Invited to an Interview! 🎉</div>
            <div class="content">
                <p>Dear Candidate,</p>
                <p>Congratulations! You have been selected for an interview for the role of <strong>{job_title}</strong>.</p>
                <p>Click the button below to join your interview at the scheduled time:</p>
                <a href="{interview_link}" class="button">Join Interview</a>
                <p style="margin-top: 15px;">If the button doesn't work, you can also use this link:</p>
                <p><a href="{interview_link}" style="color: #3b82f6;">{interview_link}</a></p>
            </div>
            <div class="divider"></div>
            <div class="footer">
                <p>Best Regards,</p>
                <p><strong>Recruitment Team</strong></p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=f"Interview Scheduled for {job_title}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    fm = FastMail(mail_config)
    await fm.send_message(message)


async def send_evaluation_report_email(email: str, name: str, job_title: str, evaluation: dict):
    """Send interview evaluation report to candidate."""
    
    subject = f"Your Interview Evaluation for {job_title} Position"
    
    # Format the violations section
    violations_text = ""
    if "violations" in evaluation:
        tab_switches = evaluation["violations"]["tab_switch_count"]
        face_violations = evaluation["violations"]["face_violation_count"]
        
        violations_text = f"""
        <h3>Interview Conduct Metrics:</h3>
        <ul>
            <li>Tab Switch Count: {tab_switches}</li>
            <li>Face Violation Count: {face_violations}</li>
        </ul>
        <p><small>These metrics indicate how many times you switched tabs or had your face absent from the camera during the interview.</small></p>
        """
    
    # Create email body with evaluation results
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4a6ea9; color: white; padding: 10px 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
            .score {{ font-size: 24px; font-weight: bold; }}
            .section {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Interview Evaluation Report</h2>
            </div>
            <div class="content">
                <p>Dear {name},</p>
                
                <p>Thank you for completing your interview for the <strong>{job_title}</strong> position. We're pleased to share your evaluation results.</p>
                
                <div class="section">
                    <h3>Your Score: <span class="score">{evaluation.get('evaluation_score', 'N/A')}</span></h3>
                </div>
                
                <div class="section">
                    <h3>Strengths:</h3>
                    <p>{evaluation.get('strengths', 'N/A')}</p>
                </div>
                
                <div class="section">
                    <h3>Areas for Improvement:</h3>
                    <p>{evaluation.get('weaknesses', 'N/A')}</p>
                </div>
                 
                {violations_text}
                
                <div class="section">
                    <h3>Feedback for You:</h3>
                    <p>{evaluation.get('feedback_for_candidate', 'N/A')}</p>
                </div>
                
                <p>The recruiter will review your evaluation and may be in touch with additional feedback or next steps.</p>
                
                <p>Best regards,<br>
                The Recruiting Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Send email
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="html"
    )
    
    fm = FastMail(mail_config)
    await fm.send_message(message)