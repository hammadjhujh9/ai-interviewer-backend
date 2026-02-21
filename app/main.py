from fastapi import FastAPI
from app.api import auth, interview, job ,resume, applications
from app.database import engine, Base
from app.models.user import User
from fastapi.middleware.cors import CORSMiddleware


Base.metadata.create_all(bind=engine)

# Create the FastAPI instance
app = FastAPI(title="Recruiter.AI Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(job.router , tags=["Job"])
app.include_router(resume.router, prefix="/candidate", tags=["Resume"])
app.include_router(applications.router, tags=["Applications"])
app.include_router(interview.router, tags=["Interview"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Recruiter.AI"}


