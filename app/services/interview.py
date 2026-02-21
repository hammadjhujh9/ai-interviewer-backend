from fastapi import WebSocket
from aiortc import RTCPeerConnection, RTCSessionDescription
from sqlalchemy.orm import Session
from app.models.interview import Interview
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.services.llm import LLMService
from app.services.stt import STTService
from app.services.tts import TTSService
from datetime import datetime

class WebRTCService:
    def __init__(self):
        self.active_sessions = {}  # {candidate_id: {job_id, websocket}}
        self.connections = {}
        self.pending_messages = {}  # {candidate_id: message}
        self.stt_service = STTService()
        self.tts_service = TTSService()
        self.llm_service = LLMService()
        self.question_pool = []
        self.conversation_history = []  # Track conversation history
        self.db = None
        self.current_interview = None
        self.application_id = None
        self.job_id = None
        self.candidate_id = None
        self.violation_logs = []  # Track violations during interview

    def set_db(self, db: Session):
        self.db = db

    def initialize_interview(self, candidate_id: int, job_id: int, application_id: int):
        self.active_sessions[candidate_id] = {"job_id": job_id, "websocket": None}
        # Create a new interview record in the database
        self.job_id = job_id
        self.candidate_id = candidate_id
        self.application_id = application_id
        self.current_interview = Interview(
            application_id=application_id,
            candidate_id=candidate_id,
            job_id=job_id,
            conversation_log=[]
        )
        
        self.db.add(self.current_interview)
        self.db.commit()
        self.db.refresh(self.current_interview)

    def save_conversation_to_db(self):
        if self.current_interview:
            self.current_interview = self.db.merge(self.current_interview)
            self.current_interview.conversation_log = self.conversation_history
            self.db.commit()

    async def broadcast_message(self, message: dict):
        self.save_conversation_to_db()

        # Broadcast the message to all active connections
        for websocket, connection in self.connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Failed to send message to a WebSocket: {e}")

    def initialize_questions(self, job: Job, resume: str):
        self.question_pool = self.llm_service.generate_questions_pool(job, resume)

    async def start_interview(self, job: Job, candidate_resume: str):
        self.job = job
        self.candidate_resume = candidate_resume
        self.initialize_questions(job, candidate_resume)
        first_question = self.llm_service.generate_next_question("", [], self.question_pool, job, candidate_resume)
        if first_question:
            self.conversation_history.append({"role": "interviewer", "message": first_question})
            print(f"First question: {first_question}")
            await self.broadcast_message({"type": "question", "question": first_question})
            audio_content = self.tts_service.synthesize_speech(first_question)
            await self.broadcast_message({"type": "audio", "audio_data": audio_content})
            return audio_content
        else:
            await self.broadcast_message({"type": "error", "message": "Failed to start interview"})
     
    async def process_response(self, response):
        try:
            # Add candidate's response to the history
            response_text = await self.handle_audio(response)
            print(f"Transcript: {response_text}")
            
            # Extract job and resume details from the database
            job = self.db.query(Job).filter(Job.job_id == self.job_id).first()
            resume = self.db.query(Resume).filter(Resume.user_id == self.candidate_id).first()

            next_question = self.llm_service.generate_next_question(
                response_text, 
                self.conversation_history,
                self.question_pool,
                job,
                resume
            )
            
            self.conversation_history.append({"role": "candidate", "message": response_text})

            if next_question:
                self.conversation_history.append({"role": "interviewer", "message": next_question})
                await self.broadcast_message({"type": "question", "question": next_question})
                
                # Generate and send TTS audio
                audio_content = self.tts_service.synthesize_speech(next_question)
                await self.broadcast_message({"type": "audio", "audio_data": audio_content})
            else:
                await self.broadcast_message({"type": "end", "message": "Interview complete."})
        except Exception as e:
            print(f"Error processing response: {e}")
            await self.broadcast_message({"type": "error", "message": "An error occurred during the interview."})
            
    async def handle_audio(self, audio_bytes: str):
        try:
            transcript = self.stt_service.transcribe_audio(audio_bytes)
            print(f"Transcript in handle_audio: {transcript}")
            return transcript
        except Exception as e:
            print(f"Error in STT: {e}")
            return None

    async def record_violation(self, violation_type: str, message: str):
        """Record a violation in the interview session"""
        if not self.current_interview:
            print("Cannot record violation: Interview not initialized")
            return False

        try:
            # Create a violation record
            violation_record = {
                "type": violation_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add to local violations log
            self.violation_logs.append(violation_record)
            
            # Update the interview record in the database
            if self.db:
                self.current_interview = self.db.merge(self.current_interview)
                
                # Update the appropriate counter based on violation type
                if violation_type == "tab_switched":
                    self.current_interview.tab_switch_count += 1
                elif violation_type == "face_violation":
                    self.current_interview.face_violation_count += 1
                
                # Store all violations in a JSON field if available
                if hasattr(self.current_interview, 'violation_logs'):
                    self.current_interview.violation_logs = self.violation_logs
                    
                # Commit immediately to ensure data is saved
                self.db.commit()
                print(f"Violation recorded: {violation_type} - {message}")
                return True
                
        except Exception as e:
            print(f"Error recording violation: {e}")
            try:
                self.db.rollback()
            except:
                pass
            return False

    async def handle_signaling(self, websocket: WebSocket):
        # await websocket.accept()
        pc = RTCPeerConnection()

        @pc.on("track")
        async def on_track(track):
            if track.kind == "audio":
                # Process audio track
                audio_data = await track.recv()
                transcript = await self.handle_audio(audio_data)
                if transcript:
                    await self.process_response(transcript)

        self.connections[websocket] = pc

        try:
            while True:
                message = await websocket.receive_json()
                if message["type"] == "offer":
                    offer = RTCSessionDescription(
                        sdp=message["sdp"], type=message["type"]
                    )
                    await pc.setRemoteDescription(offer)
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)
                    await websocket.send_json(
                        {"type": "answer", "sdp": pc.localDescription.sdp}
                    )
                elif message["type"] == "candidate":
                    candidate = message["candidate"]
                    await pc.addIceCandidate(candidate)
                elif message["type"] == "response":
                    # Handle application-specific JSON messages
                    response = message["response"]
                    await self.process_response(response)
                elif message["type"] == "violation":
                    # Handle violation messages from frontend
                    violation_type = message.get("violation")
                    violation_message = message.get("message", "No message provided")
                    
                    if violation_type in ["tab_switched", "face_violation"]:
                        success = await self.record_violation(violation_type, violation_message)
                        # Optionally send acknowledgment back to frontend
                        await websocket.send_json({
                            "type": "violation_recorded",
                            "violation": violation_type,
                            "success": success
                        })
                else:
                    # Handle unexpected JSON messages
                    print(f"Unknown message type received: {message}")
        except Exception as e:
            print(f"WebSocket closed: {e}")
            await pc.close()
            if websocket in self.connections:
                del self.connections[websocket]

    def get_active_session(self, candidate_id: int) -> dict:
        return self.active_sessions.get(candidate_id)

    def cleanup_session(self, candidate_id: int):
        if candidate_id in self.active_sessions:
            del self.active_sessions[candidate_id]

    def set_pending_message(self, candidate_id: int, message: dict):
        self.pending_messages[candidate_id] = message

    def get_pending_message(self, candidate_id: int) -> dict:
        return self.pending_messages.get(candidate_id)

    def clear_pending_message(self, candidate_id: int):
        if candidate_id in self.pending_messages:
            del self.pending_messages[candidate_id]