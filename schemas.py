from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

# Restrict status to exactly what the assignment allows
class StatusEnum(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True # Tells Pydantic to read SQLAlchemy models

class Token(BaseModel):
    access_token: str
    token_type: str

# --- TASK SCHEMAS ---
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    deadline: Optional[datetime] = None
    status: StatusEnum = StatusEnum.not_started

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    deadline: Optional[datetime] = None
    status: Optional[StatusEnum] = None
    position: Optional[int] = None

class TaskResponse(TaskCreate):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    position: int

    class Config:
        from_attributes = True