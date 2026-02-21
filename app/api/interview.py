from fastapi import APIRouter, Depends, WebSocket, HTTPException
from fastapi.websockets import WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import Job
from app.models.user import User
from app.services.interview import WebRTCService
from sqlalchemy.orm import Session
from app.models.job_application import JobApplication, ApplicationStatus
from app.api.auth import get_current_candidate
from app.services.job import get_job_by_id
from app.services.evaluation import evaluate_interview
from app.models.interview import Interview
from datetime import datetime

router = APIRouter()

# Initialize single WebRTCService instance with None for db
# We'll set it in each request using a method
webrtc_service = WebRTCService()

def verify_interview_eligibility(application: JobApplication) -> JobApplication:
    """
    Verify if candidate is eligible for interview based on job application status
    """
        
    if application.status != ApplicationStatus.INTERVIEW_SCHEDULED:
        raise HTTPException(
            status_code=403,
            detail=f"Interview not scheduled. Current application status: {application.status}"
        )
        
    return application

@router.post("/interview/start/{application_id}")
async def start_interview(
    application_id: int,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    # Fetch application to get candidate_id and job_id
    application = db.query(JobApplication).filter(JobApplication.application_id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    candidate_id = current_candidate.id
    if application.candidate_id != candidate_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this application")

    job_id = application.job_id

    # Check if interview already in progress
    # if webrtc_service.get_active_session(candidate_id):
    #     raise HTTPException(status_code=400, detail="Interview already in progress")

    # Verify interview eligibility
    verify_interview_eligibility(application)

    job_in_db = db.query(Job).filter(Job.job_id == job_id).first()
    if not job_in_db:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate = db.query(User).filter(User.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate_resume = candidate.resume

    # Set db for this request
    webrtc_service.set_db(db)
    webrtc_service.initialize_interview(candidate_id, job_id, application_id)
    first_question = await webrtc_service.start_interview(job_in_db, candidate_resume)

    # Save the first question as pending
    webrtc_service.set_pending_message(candidate_id, {"type": "audio", "audio_data": first_question})

    # Update application status
    application.status = ApplicationStatus.INTERVIEW_SCHEDULED
    db.commit()

    return {
        "status": "success",
        "message": "Interview started",
        "candidate_id": candidate_id
    }

@router.websocket("/interview/ws/{application_id}")
async def interview_websocket(
    websocket: WebSocket, 
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for handling interview signaling and audio streaming.
    """
    try:
        # Fetch application to get candidate_id
        application = db.query(JobApplication).filter(JobApplication.application_id == application_id).first()
        if not application:
            await websocket.close(code=4000, reason="Invalid application ID")
            return
        
        candidate_id = application.candidate_id

        # Verify active interview session
        session = webrtc_service.get_active_session(candidate_id)
        if not session:
            await websocket.close(code=4000, reason="No active interview session")
            return

        # Set db for this request
        webrtc_service.set_db(db)

        # Update session with websocket
        session["websocket"] = websocket
        await websocket.accept()

        # Send pending first question if exists
        pending_message = webrtc_service.get_pending_message(candidate_id)
        if pending_message:
            await websocket.send_json(pending_message)
            webrtc_service.clear_pending_message(candidate_id)

        await webrtc_service.handle_signaling(websocket)

    except WebSocketDisconnect:
        print("WebSocket disconnected")
        webrtc_service.cleanup_session(candidate_id)
    except Exception as e:
        print(f"Error during WebSocket connection: {e}")
        webrtc_service.cleanup_session(candidate_id)


@router.post("/interview/evaluate/{application_id}")
def evaluate_interview_api(
    application_id: int,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """API endpoint to trigger interview evaluation using application_id."""
    # Find the interview associated with this application
    interview = db.query(Interview).filter(Interview.application_id == application_id).first()
    
    if not interview:
        return {"status": "failed", "message": "No interview found for this application"}
    
    # Verify that the logged-in candidate is the one who conducted the interview
    application = db.query(JobApplication).filter(JobApplication.application_id == application_id).first()
    if not application or application.candidate_id != current_candidate.id:
        return {"status": "failed", "message": "Unauthorized access to this interview evaluation"}
    
    # Call the evaluate_interview function with the interview id
    result = evaluate_interview(db, interview.id)
    
    if "error" in result:
        return {"status": "failed", "message": result["error"]}
    
    return {"status": "success", "evaluation": result}

@router.post("/interview/end/{application_id}")
async def end_interview(
    application_id: int,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Ends the interview and triggers evaluation."""

    # Find the interview associated with this application
    interview = db.query(Interview).filter(Interview.application_id == application_id).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="No interview found for this application")
    
    # Verify that the logged-in candidate is the one who conducted the interview
    application = db.query(JobApplication).filter(JobApplication.application_id == application_id).first()
    if not application or application.candidate_id != current_candidate.id:
        raise HTTPException(status_code=403, detail="You are not authorized to end this interview")
    
    # Update application status to INTERVIEW_COMPLETED - use the value, not the name
    application.status = ApplicationStatus.INTERVIEW_COMPLETED
    
    # Update interview info
    interview.completed = True
    interview.updated_at = datetime.utcnow()

    db.commit()
    
    # Start evaluation process
    try:
        # Call evaluate_interview in background
        result = await evaluate_interview(db, interview.id)
        
        # Include violation counts in the response
        violation_data = {}
        if hasattr(interview, 'tab_switch_count'):
            violation_data['tab_switch_count'] = interview.tab_switch_count
        if hasattr(interview, 'face_violation_count'):
            violation_data['face_violation_count'] = interview.face_violation_count
        
        return {
            "status": "success", 
            "message": "Interview ended and evaluation started",
            "violations": violation_data
        }
    except Exception as e:
        return {"status": "partial", "message": f"Interview ended but evaluation failed: {str(e)}"}
