from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import database
import models

# --- SECURITY CONFIGURATION ---
# Real-world key is in .env file, we keep it here as its an assignment only
SECRET_KEY = "super_secret_jmd_assignment_key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Token valid only for 60 minutes

# Tells Passlib to use the bcrypt algorithm to hash passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# We tell Swagger UI where the login is actually present
# This makes the "Authorize" button in our docs to work automatically!
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- PASSWORD HASHING ---
def verify_password(plain_password, hashed_password):
    """Checks if the provided password matches the hashed one in the DB."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hashes a raw password before saving it to the DB."""
    return pwd_context.hash(password)

# --- JWT GENERATION ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates the JSON Web Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # The token expiry time is attached
    to_encode.update({"exp": expire})
    
    # Generate and return the encoded JWT string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- ROUTE PROTECTION DEPENDENCY  ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """
    Attach this to any route that requires a user to be logged in.
    It intercepts the request, reads the JWT, verifies it, and returns the User object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token to get the user's email (which we will save under 'sub')
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError: 
        # If the token is fake, tampered with, or expired, reject the request
        raise credentials_exception
        
    # Fetch the user from the database
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user