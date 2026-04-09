# Jira-like Task Management API

## Overview

This is a backend API for a Jira-like task management system built using FastAPI.
It supports user authentication, task management, and dashboard analytics.

## Tech Stack
- FastAPI
- SQLite
- SQLAlchemy
- JWT Authentication (PyJWT)
- Passlib (bcrypt)

## Setup Instructions
'''bash 
git clone <your-repo-link>
cd jira-backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload
'''
