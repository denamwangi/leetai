from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
import os
from dotenv import load_dotenv

# Import our modules
from database import get_db, create_tables, Problem, Submission, DailyPlan
from schemas import (
    Problem as ProblemSchema,
    ProblemCreate,
    Submission as SubmissionSchema,
    SubmissionCreate,
    DailyPlan as DailyPlanSchema,
    DailyPlanCreate,
    DailyPlanRequest,
    SyncResponse,
    HealthCheck,
    ErrorResponse
)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="LeetCode Study Assistant API",
    description="AI-powered LeetCode study planning and progress tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event - create database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify service and database status"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        database_connected = True
    except Exception:
        database_connected = False
    
    return HealthCheck(
        status="healthy" if database_connected else "unhealthy",
        database_connected=database_connected
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LeetCode Study Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# API Endpoints as specified in project plan
@app.get("/api/problems", response_model=List[ProblemSchema])
async def get_problems(db: Session = Depends(get_db)):
    """List all problems (for reference)"""
    problems = db.query(Problem).all()
    return problems


@app.post("/api/sync", response_model=SyncResponse)
async def sync_leetcode_data(db: Session = Depends(get_db)):
    """Fetch latest from LeetCode, create submissions (placeholder for Phase 2)"""
    # This will be implemented in Phase 2
    return SyncResponse(
        new_problems=0,
        new_submissions=0,
        message="Sync functionality will be implemented in Phase 2"
    )


@app.get("/api/stats")
async def get_overall_stats(db: Session = Depends(get_db)):
    """Overall statistics (placeholder for Phase 3)"""
    # This will be implemented in Phase 3
    return {
        "message": "Statistics functionality will be implemented in Phase 3",
        "total_problems": db.query(Problem).count(),
        "total_submissions": db.query(Submission).count()
    }


@app.get("/api/stats/topics")
async def get_topic_stats(db: Session = Depends(get_db)):
    """All topic breakdowns (placeholder for Phase 3)"""
    # This will be implemented in Phase 3
    return {
        "message": "Topic statistics functionality will be implemented in Phase 3"
    }


@app.get("/api/stats/topics/{topic}")
async def get_specific_topic_stats(topic: str, db: Session = Depends(get_db)):
    """Specific topic details (placeholder for Phase 3)"""
    # This will be implemented in Phase 3
    return {
        "message": f"Topic details for '{topic}' will be implemented in Phase 3",
        "topic": topic
    }


@app.get("/api/daily-plan")
async def get_daily_plan(
    date: Optional[date] = None,
    time_minutes: Optional[int] = None,
    custom_instructions: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get plan for date (or generate if doesn't exist) (placeholder for Phase 4)"""
    # This will be implemented in Phase 4
    # Query params: ?date=YYYY-MM-DD&time_minutes=60&custom_instructions=...
    return {
        "message": "Daily plan generation will be implemented in Phase 4",
        "requested_date": date or datetime.now().date(),
        "time_minutes": time_minutes,
        "custom_instructions": custom_instructions
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return ErrorResponse(
        error="Not Found",
        detail="The requested resource was not found"
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return ErrorResponse(
        error="Internal Server Error",
        detail="An unexpected error occurred"
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
