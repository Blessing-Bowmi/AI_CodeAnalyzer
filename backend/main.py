"""
Intelligent Code Dependency Mapping & Automated Refactoring System
FastAPI Backend Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db
from routes.auth import router as auth_router
from routes.projects import router as projects_router
from routes.admin import router as admin_router

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Code Analyzer API",
    description="Intelligent Code Dependency Mapping & Automated Refactoring System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(admin_router)

# Create uploads directory
os.makedirs(os.path.join(os.path.dirname(__file__), "uploads"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "extracted"), exist_ok=True)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Code Analyzer API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
