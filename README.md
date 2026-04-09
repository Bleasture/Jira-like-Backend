# 🚀 Jira-like Task Management API

## 📌 Overview
This project is a backend API for a Jira-like task management system built using **FastAPI**.  
It supports user authentication, task management, and dashboard analytics.

---

## ⚙️ Tech Stack
- FastAPI
- SQLite
- SQLAlchemy
- JWT Authentication (PyJWT)
- Passlib (bcrypt)

---

## ▶️ Setup Instructions

```bash
git clone <your-repo-link>
cd jira-backend

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt

uvicorn main:app --reload
```
## API Docs
Open:
```bash
http://127.0.0.1:8000/docs
```
Authentication
- Register → `/register`
- Login → `/login`
- Use token in headers:
  ```bash
  Authorization: Bearer <token>
  ```
## Features
- User Management
  Register user
  Login user
  Get all users
- Task Management
  Create task
  Get tasks
  Update task (status/position)
  Delete task
  Filter tasks
- Dashboard
  Total tasks
  Tasks by status
  Overdue tasks
  Completion percentage

## Database Schema
- Users Table
  id
  name
  email
  hashed_password
- Tasks Table
  id
  title
  description
  status
  position
  deadline
  created_by
  assigned_to
  created_at
  updated_at
