from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
import os
from dotenv import load_dotenv

# Import our modules
from database import get_db, create_tables, Problem, Submission, DailyPlan
from leetcode import LeetCodeClient
from analytics import (
    calculate_overall_stats,
    calculate_topic_stats,
    get_topic_stats_by_name,
)
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
    ErrorResponse,
    OverallStats,
    TopicStats,
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
async def sync_leetcode_data(
    limit: int = Query(20, ge=1, le=50),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Fetch latest from LeetCode, upsert problems and insert new submissions.

    - Rate limited to once every 60 seconds (naive, in-memory)
    - Supports dry-run mode to preview counts without writing
    """
    # In-memory naive rate limiter
    global _LAST_SYNC_AT  # type: ignore
    try:
        MIN_SYNC_SECONDS = 60
        now = datetime.now()
        if '_LAST_SYNC_AT' in globals() and _LAST_SYNC_AT is not None:
            delta = (now - _LAST_SYNC_AT).total_seconds()
            if delta < MIN_SYNC_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Sync allowed once every {MIN_SYNC_SECONDS}s. Try again in {int(MIN_SYNC_SECONDS - delta)}s."
                )
    except Exception:
        # If any issue with rate limiter state, proceed without blocking
        pass

    client = LeetCodeClient()
    try:
        fetched = client.fetch_recent_submissions(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LeetCode fetch failed: {e}")

    if not fetched:
        # Could be missing username/session; still return a valid response
        return SyncResponse(new_problems=0, new_submissions=0, message="No submissions fetched. Check LEETCODE_USERNAME/LEETCODE_SESSION.")

    new_problems_count = 0
    new_submissions_count = 0

    # Map existing problems by leetcode_number for quick lookup
    existing_problems = {
        p.leetcode_number: p for p in db.query(Problem).all()
    }

    # Prepare write operations
    for item in fetched:
        leetcode_number = int(item["leetcode_number"]) if isinstance(item["leetcode_number"], str) else item["leetcode_number"]
        problem = existing_problems.get(leetcode_number)

        if problem is None:
            # Upsert new Problem
            problem = Problem(
                leetcode_number=leetcode_number,
                title=item.get("title", ""),
                difficulty=item.get("difficulty", "medium"),
                topics=item.get("topics", []) or ["Unknown"],
                leetcode_url=item.get("leetcode_url", "")
            )
            if not dry_run:
                db.add(problem)
                db.flush()  # get id
            new_problems_count += 1
            existing_problems[leetcode_number] = problem

        # Insert Submission if not exists for (problem_id, solved_date)
        solved_date = item.get("solved_date")
        if not dry_run:
            existing_submission = (
                db.query(Submission)
                .filter(Submission.problem_id == problem.id)
                .filter(Submission.solved_date == solved_date)
                .first()
            )
        else:
            existing_submission = None

        if existing_submission is None:
            new_submissions_count += 1
            if not dry_run:
                sub = Submission(
                    problem_id=problem.id,
                    solved_date=solved_date,
                    attempts=1,
                )
                db.add(sub)

    if not dry_run:
        db.commit()
        # Mark sync time
        _set_last_sync()

    message = (
        f"dry-run: {dry_run}. Added problems: {new_problems_count}, submissions: {new_submissions_count}."
        if dry_run
        else f"Added problems: {new_problems_count}, submissions: {new_submissions_count}."
    )
    return SyncResponse(
        new_problems=new_problems_count,
        new_submissions=new_submissions_count,
        message=message,
    )


def _set_last_sync():
    global _LAST_SYNC_AT  # type: ignore
    _LAST_SYNC_AT = datetime.now()


@app.get("/api/stats", response_model=OverallStats)
async def get_overall_stats_endpoint(db: Session = Depends(get_db)):
    """Overall statistics calculated on-demand."""
    return calculate_overall_stats(db)


@app.get("/api/stats/topics", response_model=List[TopicStats])
async def get_topic_stats_endpoint(db: Session = Depends(get_db)):
    """All topic breakdowns with weighted scores and time windows."""
    return calculate_topic_stats(db)


@app.get("/api/stats/topics/{topic}", response_model=TopicStats)
async def get_specific_topic_stats(topic: str, db: Session = Depends(get_db)):
    """Specific topic details by name."""
    stats = get_topic_stats_by_name(db, topic)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Topic '{topic}' not found")
    return stats


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
