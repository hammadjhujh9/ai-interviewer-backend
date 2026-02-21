from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Load .env so app.database gets correct DATABASE_URL
from dotenv import load_dotenv
load_dotenv(".env")

from app.database import Base
from app.models.user import User, Candidate, Recruiter
from app.models.resume import Resume
from app.models.job import Job
from app.models.job_application import JobApplication
from app.models.suitability import CandidateJobSuitability
from app.models.interview import Interview
from app.models.interview_evaluation import InterviewEvaluation

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        connectable = create_engine(
            database_url,
            poolclass=pool.NullPool,
            connect_args={"connect_timeout": 10},
        )
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            connect_args={"connect_timeout": 10},
        )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
