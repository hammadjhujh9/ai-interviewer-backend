import os
from datetime import datetime, timedelta
from typing import Union
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.database import SessionLocal, get_db
from app.schemas.user import CandidateCreate, RecruiterCreate, UserLogin, UserLoginResponse, UserResponse
from app.services.user import create_user, get_user_by_email
from app.models.user import User, UserRole


router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")  # This will look for the 'login' route to obtain the token

SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")  # Change this for production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Set token expiration time (in minutes)

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

def verify_token(token: str):
    try:
        # print(f"Decoding token: {token}")  # Debug statement
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print(f"Decoded payload: {payload}")  # Debug statement
        return payload
    except JWTError as e:
        print(f"JWTError: {e}")  # Debug statement
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Secure route for getting current candidate user
def get_current_candidate(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token)
    user_id = payload.get("sub")  # 'sub' is the user ID stored in the token
    if user_id is None:
        print("User ID is None")
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.role != UserRole.candidate:
        print("User is not candidate or does not exist")
        raise credentials_exception
    # print(f"User ID: {user.id}, Role: {user.role}")
    return user

# Secure route for getting current recruiter user
def get_current_recruiter(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.role != UserRole.recruiter:
        raise credentials_exception
    return user
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "sub": str(data["sub"])})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Candidate Signup Route
@router.post("/candidate/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def candidate_signup(user: CandidateCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = create_user(db, user)
    return new_user

# Recruiter Signup Route
@router.post("/recruiter/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def recruiter_signup(user: RecruiterCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    return new_user

# Unified Login Route
@router.post("/login", response_model=UserLoginResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": db_user.id}, expires_delta=access_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }


# Example of a secure route for candidate (to access only after login)
@router.get("/candidate/profile")
def get_candidate_profile(current_user: User = Depends(get_current_candidate)):
    return {"user": current_user}

# Example of a secure route for recruiter (to access only after login)
@router.get("/recruiter/profile")
def get_recruiter_profile(current_user: User = Depends(get_current_recruiter)):
    return {"user": current_user}
