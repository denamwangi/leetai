#!/usr/bin/env python3
"""
CSV Import Script for LeetCode Study Assistant

This script imports historical LeetCode data from a CSV file into the database.
CSV format: leetcode_number,title,difficulty,solved_date,attempts,topics

Usage:
    python import_csv.py [csv_file_path]
    
If no file path is provided, it will look for data/historical.csv
"""

import csv
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, create_tables, Problem, Submission


def parse_csv_row(row: Dict[str, str]) -> tuple[Dict, Dict]:
    """
    Parse a CSV row and return problem and submission data dictionaries.
    
    Args:
        row: Dictionary with CSV row data
        
    Returns:
        Tuple of (problem_data, submission_data)
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # Parse basic fields
        leetcode_number = int(row['leetcode_number'])
        title = row['title'].strip()
        difficulty = row['difficulty'].strip().lower()
        solved_date = datetime.strptime(row['solved_date'], '%Y-%m-%d').date()
        attempts = int(row['attempts'])
        
        # Parse topics (pipe-separated)
        topics_str = row['topics'].strip()
        topics = [topic.strip() for topic in topics_str.split('|') if topic.strip()]
        
        # Validate difficulty
        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid difficulty: {difficulty}")
        
        # Create LeetCode URL
        leetcode_url = f"https://leetcode.com/problems/{title.lower().replace(' ', '-')}/"
        
        # Create data dictionaries
        problem_data = {
            'leetcode_number': leetcode_number,
            'title': title,
            'difficulty': difficulty,
            'topics': topics,
            'leetcode_url': leetcode_url
        }
        
        submission_data = {
            'problem_id': 0,  # Will be updated after problem insertion
            'solved_date': solved_date,
            'attempts': attempts
        }
        
        return problem_data, submission_data
        
    except KeyError as e:
        raise ValueError(f"Missing required field: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid data format: {e}")


def import_csv_data(csv_file_path: str) -> Dict[str, int]:
    """
    Import data from CSV file into the database.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        Dictionary with import statistics
    """
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    # Create database tables
    create_tables()
    
    stats = {
        'problems_created': 0,
        'submissions_created': 0,
        'problems_skipped': 0,
        'submissions_skipped': 0,
        'errors': 0
    }
    
    db: Session = SessionLocal()
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Validate CSV headers
            required_headers = ['leetcode_number', 'title', 'difficulty', 'solved_date', 'attempts', 'topics']
            if not all(header in reader.fieldnames for header in required_headers):
                raise ValueError(f"CSV must contain headers: {required_headers}")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                try:
                    # Parse the row
                    problem_data, submission_data = parse_csv_row(row)
                    
                    # Check if problem already exists
                    existing_problem = db.query(Problem).filter(
                        Problem.leetcode_number == problem_data['leetcode_number']
                    ).first()
                    
                    if existing_problem:
                        print(f"Row {row_num}: Problem {problem_data['leetcode_number']} already exists, skipping...")
                        stats['problems_skipped'] += 1
                        continue
                    
                    # Create problem
                    db_problem = Problem(**problem_data)
                    db.add(db_problem)
                    db.flush()  # Get the ID without committing
                    
                    # Update submission with problem_id
                    submission_data['problem_id'] = db_problem.id
                    db_submission = Submission(**submission_data)
                    db.add(db_submission)
                    
                    stats['problems_created'] += 1
                    stats['submissions_created'] += 1
                    
                    print(f"Row {row_num}: Imported {problem_data['title']} (LeetCode #{problem_data['leetcode_number']})")
                    
                except ValueError as e:
                    print(f"Row {row_num}: Error - {e}")
                    stats['errors'] += 1
                    continue
                except IntegrityError as e:
                    print(f"Row {row_num}: Database error - {e}")
                    db.rollback()
                    stats['errors'] += 1
                    continue
            
            # Commit all changes
            db.commit()
            print(f"\n✅ Import completed successfully!")
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    return stats


def print_import_summary(stats: Dict[str, int]):
    """Print a summary of the import operation."""
    print("\n" + "="*50)
    print("IMPORT SUMMARY")
    print("="*50)
    print(f"Problems created: {stats['problems_created']}")
    print(f"Submissions created: {stats['submissions_created']}")
    print(f"Problems skipped: {stats['problems_skipped']}")
    print(f"Submissions skipped: {stats['submissions_skipped']}")
    print(f"Errors: {stats['errors']}")
    print("="*50)


def main():
    """Main function to run the CSV import."""
    # Determine CSV file path
    if len(sys.argv) > 1:
        csv_file_path = sys.argv[1]
    else:
        # Default to data/historical.csv
        script_dir = Path(__file__).parent
        csv_file_path = script_dir.parent / "data" / "historical.csv"
    
    print(f"🚀 Starting CSV import from: {csv_file_path}")
    
    try:
        stats = import_csv_data(str(csv_file_path))
        print_import_summary(stats)
        
        if stats['errors'] > 0:
            print(f"\n⚠️  {stats['errors']} rows had errors. Check the output above for details.")
            sys.exit(1)
        else:
            print("\n🎉 All data imported successfully!")
            
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
