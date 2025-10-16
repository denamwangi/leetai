from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://denamwangi@localhost:5432/leetcode_assistant")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


class Problem(Base):
    """LeetCode problem model"""
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True, index=True)
    leetcode_number = Column(Integer, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # easy, medium, hard
    topics = Column(ARRAY(String), nullable=False)  # Array of LeetCode tags
    leetcode_url = Column(String, nullable=False)
    
    # Relationship to submissions
    submissions = relationship("Submission", back_populates="problem")


class Submission(Base):
    """User submission model"""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    solved_date = Column(Date, nullable=False)
    attempts = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to problem
    problem = relationship("Problem", back_populates="submissions")


class DailyPlan(Base):
    """Daily study plan model"""
    __tablename__ = "daily_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_date = Column(Date, nullable=False, index=True)
    available_time_minutes = Column(Integer, nullable=False)
    custom_instructions = Column(Text, nullable=True)  # Optional custom instructions
    problem_recommendations = Column(JSONB, nullable=False)  # Array of {leetcode_number, reason, estimated_time}
    focus_topic = Column(String, nullable=False)  # The one new topic for the day
    ai_rationale = Column(Text, nullable=False)  # Claude's explanation
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables in the database (for testing/reset)"""
    Base.metadata.drop_all(bind=engine)
