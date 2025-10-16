#!/usr/bin/env python3
"""
Script to import historical LeetCode data from JSON file into the database.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from database import Problem, Submission, DATABASE_URL

load_dotenv()

def import_historical_data(json_file: str = "../data/historical.json"):
    """Import historical data from JSON file into database"""
    
    # Load JSON data
    print(f"📖 Loading data from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data["data"]["userProgressQuestionList"]["questions"]
    print(f"✅ Found {len(questions)} problems in JSON file")
    
    # Connect to database
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            imported_problems = 0
            imported_submissions = 0
            
            for question in questions:
                # Skip if not solved
                if question.get("questionStatus") != "SOLVED":
                    continue
                
                # Extract problem data
                leetcode_number = int(question["frontendId"])
                title = question["title"]
                difficulty = question["difficulty"].lower()
                last_submitted_at = question["lastSubmittedAt"]
                num_submitted = question["numSubmitted"]
                
                # Extract topics
                topics = []
                if "topicTags" in question:
                    topics = [tag["name"] for tag in question["topicTags"]]
                
                # Parse date
                solved_date = datetime.fromisoformat(last_submitted_at.replace('Z', '+00:00')).date()
                
                # Only import 2025 data
                if solved_date.year != 2025:
                    continue
                
                # Generate titleSlug from title (convert to lowercase, replace spaces with hyphens)
                title_slug = title.lower().replace(' ', '-').replace('(', '').replace(')', '').replace(',', '').replace('.', '').replace("'", '')
                leetcode_url = f"https://leetcode.com/problems/{title_slug}/"
                
                # Insert or update problem
                problem_query = text("""
                    INSERT INTO problems (leetcode_number, title, difficulty, topics, leetcode_url)
                    VALUES (:leetcode_number, :title, :difficulty, :topics, :leetcode_url)
                    ON CONFLICT (leetcode_number) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        difficulty = EXCLUDED.difficulty,
                        topics = EXCLUDED.topics,
                        leetcode_url = EXCLUDED.leetcode_url
                """)
                
                conn.execute(problem_query, {
                    "leetcode_number": leetcode_number,
                    "title": title,
                    "difficulty": difficulty,
                    "topics": topics,
                    "leetcode_url": leetcode_url
                })
                imported_problems += 1
                
                # Get the problem ID for the submission
                problem_id_query = text("SELECT id FROM problems WHERE leetcode_number = :leetcode_number")
                result = conn.execute(problem_id_query, {"leetcode_number": leetcode_number})
                problem_row = result.fetchone()
                
                if problem_row:
                    problem_id = problem_row[0]
                    
                    # Insert submission
                    submission_query = text("""
                        INSERT INTO submissions (problem_id, solved_date, attempts)
                        VALUES (:problem_id, :solved_date, :attempts)
                    """)
                    
                    conn.execute(submission_query, {
                        "problem_id": problem_id,
                        "solved_date": solved_date,
                        "attempts": num_submitted
                    })
                imported_submissions += 1
                
                if imported_problems % 50 == 0:
                    print(f"   Processed {imported_problems} problems...")
            
            # Commit transaction
            trans.commit()
            
            print(f"✅ Successfully imported:")
            print(f"   📊 {imported_problems} problems")
            print(f"   📝 {imported_submissions} submissions")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error importing data: {e}")
            raise

if __name__ == "__main__":
    import_historical_data()
