from pydantic import BaseModel

class ApplicationReviewRequest(BaseModel):
    decision: str  # Either "approved" or "rejected"

class FinalResultRequest(BaseModel):
    result: str  # Either "accepted" or "rejected"
    feedback: str = None  # Optional feedback for the candidate
