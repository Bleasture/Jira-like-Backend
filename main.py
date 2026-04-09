from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

import models, schemas, auth
from database import engine, get_db

# SQLite Table creation if not present
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Jira-like Task Manager API")

# --- 1. USER MANAGEMENT & AUTHENTICATION ---

@app.post("/register", response_model=schemas.UserResponse, tags=["Users"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Duplicate email check
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # We hash password and save it here
    hashed_pwd = auth.get_password_hash(user.password)
    new_user = models.User(name=user.name, email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # We map the user's email to FastAPI 
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Generate the JWT token
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users", response_model=List[schemas.UserResponse], tags=["Users"])
def get_users(db: Session = Depends(get_db)):
    """Get list of users for assignment dropdown simulation"""
    return db.query(models.User).all()


# --- 2. TASK MANAGEMENT (Protected Routes) ---

@app.post("/tasks", response_model=schemas.TaskResponse, tags=["Tasks"])
def create_task(
    task: schemas.TaskCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    # We check if user is present or not
    if task.assigned_to:
        assigned_user = db.query(models.User).filter(models.User.id == task.assigned_to).first()
        if not assigned_user:
            raise HTTPException(status_code=400, detail="Assigned user does not exist")

    # Convert Pydantic schema to dictionary and add the creator's ID
    new_task = models.Task(**task.model_dump(), created_by=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/tasks", response_model=List[schemas.TaskResponse], tags=["Tasks"])
def get_tasks(
    status: Optional[str] = None, 
    assigned_to: Optional[int] = None, 
    deadline: Optional[datetime] = None, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Filter tasks by status, assigned user, or deadline."""
    query = db.query(models.Task)
    
    if status:
        query = query.filter(models.Task.status == status)
    if assigned_to:
        query = query.filter(models.Task.assigned_to == assigned_to)
    if deadline:
        # Task fetching based on deadline
        query = query.filter(models.Task.deadline <= deadline)
        
    return query.all()

@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse, tags=["Tasks"])
def update_task(
    task_id: int, 
    task_update: schemas.TaskUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Jira based Move Logic: Updates status, position, or any other field."""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # We check if assigned user exists
    if task_update.assigned_to:
        assigned_user = db.query(models.User).filter(models.User.id == task_update.assigned_to).first()
        if not assigned_user:
            raise HTTPException(status_code=400, detail="Assigned user does not exist")
    
    # Here we update only the fields sent to update
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}", tags=["Tasks"])
def delete_task(
    task_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Deletes a task by its ID."""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    
    return {"detail": "Task successfully deleted"}


# --- 3. DASHBOARD ANALYTICS ---

@app.get("/dashboard", tags=["Dashboard"])
def get_dashboard(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    tasks = db.query(models.Task).all()
    total_tasks = len(tasks)
    
    status_counts = {"not_started": 0, "in_progress": 0, "completed": 0}
    user_assignments = {}
    overdue_count = 0
    now = datetime.utcnow()
    
    for t in tasks:
        # 1. Tally statuses
        status_counts[t.status] = status_counts.get(t.status, 0) + 1
        
        # 2. Tally user assignments
        if t.assigned_to:
            user_assignments[t.assigned_to] = user_assignments.get(t.assigned_to, 0) + 1
            
        # 3. Deadline check
        if t.deadline and t.deadline < now and t.status != "completed":
            overdue_count += 1

    completed = status_counts.get("completed", 0)
    completion_percentage = (completed / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        "total_tasks": total_tasks,
        "status_counts": status_counts,
        "overdue_tasks": overdue_count,
        "tasks_assigned_to_users": user_assignments,
        "completed_tasks": completed,
        "completion_percentage": round(completion_percentage, 2)
    }