#!/usr/bin/env python3
"""
Script to import historical LeetCode data from CSV file into the database.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from database import Problem, Submission, DATABASE_URL

load_dotenv()

def import_historical_csv(csv_file: str = "../data/historical.csv"):
    """Import historical data from CSV file into database"""
    
    # Load CSV data
    print(f"📖 Loading data from {csv_file}...")
    
    imported_problems = 0
    imported_submissions = 0
    
    # Connect to database
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Skip empty rows
                    if not row.get('leetcode_number'):
                        continue
                    
                    # Extract data
                    leetcode_number = int(row['leetcode_number'])
                    title = row['title']
                    difficulty = row['difficulty'].lower()
                    solved_date = datetime.strptime(row['solved_date'], '%Y-%m-%d').date()
                    attempts = int(row['attempts'])
                    
                    # Parse topics (pipe-separated string)
                    topics_str = row.get('topics', '')
                    topics = [topic.strip() for topic in topics_str.split('|') if topic.strip()]
                    
                    # Generate LeetCode URL (convert title to slug)
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
                            "attempts": attempts
                        })
                        imported_submissions += 1
                    
                    if imported_problems % 20 == 0:
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
    import_historical_csv()
