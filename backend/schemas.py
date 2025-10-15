from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class DifficultyEnum(str, Enum):
    """Difficulty levels for LeetCode problems"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# Base schemas for database models
class ProblemBase(BaseModel):
    """Base schema for LeetCode problems"""
    leetcode_number: int = Field(..., description="LeetCode problem number")
    title: str = Field(..., min_length=1, description="Problem title")
    difficulty: DifficultyEnum = Field(..., description="Problem difficulty level")
    topics: List[str] = Field(..., min_items=1, description="List of topic tags")
    leetcode_url: str = Field(..., description="URL to the problem on LeetCode")
    
    @validator('leetcode_number')
    def validate_leetcode_number(cls, v):
        if v <= 0:
            raise ValueError('LeetCode number must be positive')
        return v
    
    @validator('topics')
    def validate_topics(cls, v):
        if not v or any(not topic.strip() for topic in v):
            raise ValueError('Topics cannot be empty or contain empty strings')
        return [topic.strip() for topic in v]


class ProblemCreate(ProblemBase):
    """Schema for creating a new problem"""
    pass


class Problem(ProblemBase):
    """Schema for problem response"""
    id: int
    
    class Config:
        from_attributes = True


class SubmissionBase(BaseModel):
    """Base schema for submissions"""
    problem_id: int = Field(..., description="ID of the problem")
    solved_date: date = Field(..., description="Date when problem was solved")
    attempts: int = Field(1, ge=1, description="Number of attempts to solve")
    
    @validator('solved_date')
    def validate_solved_date(cls, v):
        if v > date.today():
            raise ValueError('Solved date cannot be in the future')
        return v


class SubmissionCreate(SubmissionBase):
    """Schema for creating a new submission"""
    pass


class Submission(SubmissionBase):
    """Schema for submission response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubmissionWithProblem(Submission):
    """Schema for submission response with problem details"""
    problem: Optional[Problem] = None


# Analytics and statistics schemas
class TopicStats(BaseModel):
    """Schema for topic statistics"""
    topic: str = Field(..., description="Topic name")
    easy_3d: int = Field(0, ge=0, description="Easy problems solved in last 3 days")
    medium_3d: int = Field(0, ge=0, description="Medium problems solved in last 3 days")
    hard_3d: int = Field(0, ge=0, description="Hard problems solved in last 3 days")
    easy_7d: int = Field(0, ge=0, description="Easy problems solved in last 7 days")
    medium_7d: int = Field(0, ge=0, description="Medium problems solved in last 7 days")
    hard_7d: int = Field(0, ge=0, description="Hard problems solved in last 7 days")
    easy_14d: int = Field(0, ge=0, description="Easy problems solved in last 14 days")
    medium_14d: int = Field(0, ge=0, description="Medium problems solved in last 14 days")
    hard_14d: int = Field(0, ge=0, description="Hard problems solved in last 14 days")
    easy_28d_plus: int = Field(0, ge=0, description="Easy problems solved 28+ days ago")
    medium_28d_plus: int = Field(0, ge=0, description="Medium problems solved 28+ days ago")
    hard_28d_plus: int = Field(0, ge=0, description="Hard problems solved 28+ days ago")
    last_solved_date: Optional[date] = Field(None, description="Last date this topic was practiced")
    weighted_score: float = Field(0.0, ge=0.0, description="Calculated weighted score for this topic")


class OverallStats(BaseModel):
    """Schema for overall statistics"""
    total_problems_solved: int = Field(0, ge=0, description="Total number of problems solved")
    total_attempts: int = Field(0, ge=0, description="Total number of attempts")
    easy_solved: int = Field(0, ge=0, description="Number of easy problems solved")
    medium_solved: int = Field(0, ge=0, description="Number of medium problems solved")
    hard_solved: int = Field(0, ge=0, description="Number of hard problems solved")
    unique_topics_practiced: int = Field(0, ge=0, description="Number of unique topics practiced")
    current_streak_days: int = Field(0, ge=0, description="Current daily solving streak")
    longest_streak_days: int = Field(0, ge=0, description="Longest daily solving streak")
    average_attempts_per_problem: float = Field(0.0, ge=0.0, description="Average attempts per problem")


# Daily plan schemas
class ProblemRecommendation(BaseModel):
    """Schema for problem recommendations in daily plans"""
    leetcode_number: int = Field(..., description="LeetCode problem number")
    title: str = Field(..., description="Problem title")
    difficulty: DifficultyEnum = Field(..., description="Problem difficulty")
    reason: str = Field(..., description="AI's reason for recommending this problem")
    estimated_minutes: int = Field(..., ge=1, le=120, description="Estimated time to solve in minutes")
    leetcode_url: str = Field(..., description="URL to the problem on LeetCode")


class DailyPlanBase(BaseModel):
    """Base schema for daily plans"""
    plan_date: date = Field(..., description="Date for the study plan")
    available_time_minutes: int = Field(..., ge=15, le=480, description="Available study time in minutes")
    focus_topic: str = Field(..., min_length=1, description="Main topic to focus on")
    recommendations: List[ProblemRecommendation] = Field(..., min_items=1, description="List of recommended problems")
    ai_rationale: str = Field(..., min_length=10, description="AI's explanation for the plan")


class DailyPlanCreate(DailyPlanBase):
    """Schema for creating a daily plan"""
    pass


class DailyPlan(DailyPlanBase):
    """Schema for daily plan response"""
    id: int
    created_at: datetime
    is_cached: bool = Field(False, description="Whether this plan was cached or newly generated")
    
    class Config:
        from_attributes = True


class DailyPlanRequest(BaseModel):
    """Schema for daily plan generation request"""
    date: Optional[date] = None
    time_minutes: int = Field(..., ge=15, le=480)
    custom_instructions: Optional[str] = Field(None, max_length=500)


# Sync and API response schemas
class SyncResponse(BaseModel):
    """Schema for sync operation response"""
    new_problems: int = Field(0, ge=0, description="Number of new problems added")
    new_submissions: int = Field(0, ge=0, description="Number of new submissions added")
    message: str = Field(..., description="Sync operation result message")
    sync_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the sync was performed")


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the error occurred")


# Health check schema
class HealthCheck(BaseModel):
    """Schema for health check response"""
    status: str = Field(..., description="Service status")
    database_connected: bool = Field(..., description="Whether database is connected")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
