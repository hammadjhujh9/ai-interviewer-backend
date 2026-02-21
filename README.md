# Recruiter AI Backend

## Overview

Recruiter AI Backend is an intelligent recruitment platform built with FastAPI that automates the job matching process. It uses AI to analyze resumes and job descriptions, calculating suitability scores to match candidates with the most appropriate positions.

## Key Features

- **User Authentication**
  - Separate authentication flows for candidates and recruiters
  - JWT-based secure authentication
  - Role-based access control

- **Recruiter Features**
  - Post, update, and delete job listings
  - View candidate applications
  - Access candidate suitability scores
  - Manage company profile

- **Candidate Features**
  - Upload and parse resumes using AI
  - View personalized job recommendations
  - Automatic suitability scoring for jobs
  - Track application status

- **AI-Powered Features**
  - Automated resume parsing using Groq API
  - Intelligent job matching algorithm
  - Real-time suitability score calculation
  - Natural language processing for job requirements

## Technology Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **AI Integration**: Groq API (LLaMA model)
- **Migration Tool**: Alembic

## Project Structure

```
recruiter_ai_backend/
├── alembic/              # Database migrations
├── app/
│   ├── api/              # API endpoints
│   │   ├── auth.py       # Authentication routes
│   │   ├── job.py        # Job-related routes
│   │   └── resume.py     # Resume-related routes
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── core/             # Core functionality
├── tests/                # Unit tests
└── .env                  # Environment variables
```

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/recruiter_ai_backend.git
    cd recruiter_ai_backend
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**
   Create a `.env` file with the following content:

    ```env
    GROQ_API_KEY=your_groq_api_key
    DATABASE_URL=postgresql://username:password@localhost/db_name
    SECRET_KEY=your_secret_key
        ```

5. **Initialize the database:**

    ```bash
    alembic upgrade head
    ```

6. **Run the application:**

    ```bash
    uvicorn app.main:app --reload
    ```

7. **Access the application:**

    - Main application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
    - API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    - Alternative API docs: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Development

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Groq API account and API key

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app

# Run specific test modules
pytest tests/api/test_auth.py
```

### Code Formatting and Linting

```bash
# Format code with black
black app tests

# Run flake8 for linting
flake8 app tests
```

## API Endpoints

### Authentication

- `POST /auth/candidate/signup` - Register a new candidate
- `POST /auth/recruiter/signup` - Register a new recruiter
- `POST /auth/candidate/login` - Candidate login
- `POST /auth/recruiter/login` - Recruiter login

### Jobs

- `POST /recruiter/jobs` - Create a new job posting
- `GET /recruiter/jobs` - List all jobs by recruiter
- `GET /recruiter/jobs/{job_id}` - Get specific job details
- `PUT /recruiter/jobs/{job_id}` - Update job posting
- `DELETE /recruiter/jobs/{job_id}` - Delete job posting

### Resumes and Profiles

- `POST /candidate/upload-resume` - Upload and parse resume
- `GET /candidate/profile` - Get candidate profile
- `PUT /candidate/profile` - Update candidate profile
- `GET /recruiter/profile` - Get recruiter profile
- `PUT /recruiter/profile` - Update recruiter profile

### Applications

- `POST /candidate/apply/{job_id}` - Apply for a job
- `GET /candidate/applications` - Get all applications by candidate
- `GET /recruiter/applications` - Get all applications for recruiter's jobs
- `PUT /recruiter/applications/{application_id}` - Update application status

## Database Schema

The application uses several key tables:

- **`users`** - Core user information (id, email, password_hash, role, created_at)
- **`candidates`** - Candidate-specific details (user_id, first_name, last_name, phone, skills)
- **`recruiters`** - Recruiter-specific details (user_id, company_name, position, company_description)
- **`jobs`** - Job postings (id, title, description, requirements, recruiter_id, location, salary_range)
- **`resumes`** - Parsed resume data (id, candidate_id, content, parsed_data, upload_date)
- **`applications`** - Job applications (id, job_id, candidate_id, status, apply_date)
- **`candidate_job_suitability`** - Calculated match scores (candidate_id, job_id, score, match_reasons)


## Troubleshooting

### Common Issues

- **Database Connection Errors**: Verify PostgreSQL is running and credentials are correct
- **JWT Authentication Failures**: Check that SECRET_KEY is properly set
- **AI Processing Errors**: Ensure GROQ_API_KEY is valid and has sufficient credits
- **Slow Performance**: Consider optimizing database queries or scaling resources

### Logs

For detailed debugging:

```bash
uvicorn app.main:app --log-level=debug
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit a pull request

Please adhere to the project's code style and include tests for new features.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please contact the project maintainers at example@example.com or open an issue on GitHub.
