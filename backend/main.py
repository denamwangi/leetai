# (moved routes below app initialization)
from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
import logging
import os
from dotenv import load_dotenv
from backend.observability import get_langfuse, start_trace, end_span, langfuse_diagnostics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import our modules
from backend.database import get_db, create_tables, Problem, Submission, DailyPlan
from backend.leetcode import LeetCodeClient
from backend.analytics import (
    calculate_overall_stats,
    calculate_topic_stats,
    get_topic_stats_by_name,
    get_recent_submissions_by_topics,
)
from backend.claude import ClaudeClient
from backend.schemas import (
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
from backend.schemas import TopicsDecision, TopicsPreviewResponse, ConfirmPlanRequest

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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],  # React dev server + Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/daily-plan/topics-preview", response_model=TopicsDecision)
async def preview_daily_plan_topics(
    request: Request,
    time_minutes: int = Query(..., ge=15, le=480),
    custom_instructions: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Run Prompt 1 only and return topics + a preview list of recent problems. Does not cache."""
    topic_stats = calculate_topic_stats(db)
    trace = start_trace(
        "http.preview_daily_plan_topics",
        user_id=str(request.client.host) if request and request.client else None,
        metadata={"path": str(request.url.path)}
    )
    claude = ClaudeClient()
    decision = claude.generate_topics_decision(topic_stats, time_minutes, custom_instructions)
    try:
        TopicsDecision(**decision)
    except Exception:
        # Basic fallback validation
        fallback_topics = sorted(topic_stats, key=lambda t: t.get("weighted_score", 0.0))
        new_topic = fallback_topics[0]["topic"] if fallback_topics else "Arrays"
        review_topics = [t["topic"] for t in fallback_topics[1:3]] if len(fallback_topics) > 1 else []
        decision = {"new_topic": new_topic, "review_topics": review_topics}

    # Do not include preview_recent; return only the decision for user review
    end_span(trace, output={"decision": decision})
    return decision


@app.post("/api/daily-plan/confirm")
async def confirm_daily_plan(body: ConfirmPlanRequest, db: Session = Depends(get_db)):
    """After user approves topics, run Prompt 2, save and return plan."""
    plan_date = body.date or datetime.now().date()

    topics = [body.decision.new_topic] + (body.decision.review_topics or [])
    recent = get_recent_submissions_by_topics(db, topics, days=30)

    claude = ClaudeClient()
    plan = claude.generate_daily_plan_from_problems(
        body.decision.dict(), recent, body.time_minutes, body.custom_instructions
    )

    focus_topic = plan.get("focus_topic") or body.decision.new_topic
    recommendations = plan.get("recommendations") or []
    ai_rationale = plan.get("rationale") or ""

    record = DailyPlan(
        plan_date=plan_date,
        available_time_minutes=body.time_minutes,
        custom_instructions=body.custom_instructions,
        problem_recommendations=recommendations,
        focus_topic=focus_topic,
        ai_rationale=ai_rationale,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "plan_date": record.plan_date,
        "available_time_minutes": record.available_time_minutes,
        "focus_topic": record.focus_topic,
        "recommendations": record.problem_recommendations,
        "ai_rationale": record.ai_rationale,
        "created_at": record.created_at,
        "is_cached": False,
    }

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
    # Initialize Langfuse if configured
    try:
        if get_langfuse() is not None:
            print("✅ Langfuse initialized")
        else:
            print("ℹ️ Langfuse not configured; skipping")
    except Exception:
        print("⚠️ Failed to initialize Langfuse")


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
        fetched = await client.fetch_recent_submissions(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LeetCode fetch failed: {e}")

    if not fetched:
        # Could be missing username/session; still return a valid response
        return SyncResponse(new_problems=0, new_submissions=0, message="No new submissions since last sync.")

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
    """Get plan for date (or generate if doesn't exist)."""
    plan_date = date or datetime.now().date()

    # If exists: return cached plan (check all parameters)
    existing = (
        db.query(DailyPlan)
        .filter(
            DailyPlan.plan_date == plan_date,
            DailyPlan.available_time_minutes == time_minutes,
            DailyPlan.custom_instructions == custom_instructions
        )
        .first()
    )
    if existing:
        return {
            "id": existing.id,
            "plan_date": existing.plan_date,
            "available_time_minutes": existing.available_time_minutes,
            "focus_topic": existing.focus_topic,
            "recommendations": existing.problem_recommendations,
            "ai_rationale": existing.ai_rationale,
            "created_at": existing.created_at,
            "is_cached": True,
        }

    if time_minutes is None:
        raise HTTPException(status_code=400, detail="time_minutes is required when generating a new plan")

    # Generate a new plan using two-step flow (Phase 7)
    topic_stats = calculate_topic_stats(db)
    try:
        claude = ClaudeClient()
        decision = claude.generate_topics_decision(topic_stats, time_minutes, custom_instructions)
        # Validate decision or fallback
        try:
            TopicsDecision(**decision)
        except Exception:
            fallback_topics = sorted(topic_stats, key=lambda t: t.get("weighted_score", 0.0))
            new_topic = fallback_topics[0]["topic"] if fallback_topics else "Arrays"
            review_topics = [t["topic"] for t in fallback_topics[1:3]] if len(fallback_topics) > 1 else []
            decision = {"new_topic": new_topic, "review_topics": review_topics}

        topics = [decision.get("new_topic")] + (decision.get("review_topics") or [])
        recent = get_recent_submissions_by_topics(db, topics, days=30)
        plan = claude.generate_daily_plan_from_problems(decision, recent, time_minutes, custom_instructions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {e}")

    # Validate and persist
    # Expecting plan keys: focus_topic, recommendations (list), rationale
    focus_topic = plan.get("focus_topic") or "General Review"
    recommendations = plan.get("recommendations") or []
    ai_rationale = plan.get("rationale") or ""

    # Persist in DailyPlan
    record = DailyPlan(
        plan_date=plan_date,
        available_time_minutes=time_minutes,
        custom_instructions=custom_instructions,
        problem_recommendations=recommendations,
        focus_topic=focus_topic,
        ai_rationale=ai_rationale,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "plan_date": record.plan_date,
        "available_time_minutes": record.available_time_minutes,
        "focus_topic": record.focus_topic,
        "recommendations": record.problem_recommendations,
        "ai_rationale": record.ai_rationale,
        "created_at": record.created_at,
        "is_cached": False,
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


@app.get("/observability/test")
async def observability_test():
    trace = start_trace("http.observability_test", metadata={"note": "manual test"})
    end_span(trace, output={"ok": True})
    return {"ok": True}


@app.get("/observability/diagnostics")
async def observability_diagnostics():
    return langfuse_diagnostics()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
