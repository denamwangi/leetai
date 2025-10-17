#!/usr/bin/env python3
"""
Script to export all historical LeetCode data to CSV format.
This fetches all submissions from your LeetCode account.
"""

import os
import csv
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class LeetCodeExporter:
    def __init__(self):
        self.session = requests.Session()
        self.session_cookie = os.getenv("LEETCODE_SESSION")
        
        if self.session_cookie:
            self.session.cookies.set("LEETCODE_SESSION", self.session_cookie, domain="leetcode.com")
            self.session.headers.update({"User-Agent": "leetcode-exporter/1.0"})
            print(f"🍪 Using LeetCode session cookie (length: {len(self.session_cookie)})")
        else:
            print("⚠️  No LEETCODE_SESSION cookie found - this will only work for public data")
    
    def fetch_all_submissions(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch all submissions from LeetCode GraphQL API"""
        query = """
        query recentAcSubmissions($username: String!, $limit: Int!) {
            recentAcSubmissionList(username: $username, limit: $limit) {
                id
                title
                titleSlug
                timestamp
                statusDisplay
                lang
                url
                isPending
                memory
                runtime
                hasNotes
                notes
                flagType
                __typename
            }
        }
        """
        
        variables = {
            "username": os.getenv("LEETCODE_USERNAME", ""),
            "limit": limit
        }
        
        response = self.session.post(
            "https://leetcode.com/graphql/",
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.status_code}")
        
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data["data"]["recentAcSubmissionList"]
    
    def fetch_problem_details(self, title_slug: str) -> Dict[str, Any]:
        """Fetch detailed problem information"""
        query = """
        query questionData($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionId
                questionFrontendId
                title
                difficulty
                likes
                dislikes
                isLiked
                similarQuestions
                contributors {
                    username
                    profileUrl
                    avatarUrl
                    __typename
                }
                topicTags {
                    name
                    slug
                    translatedName
                    __typename
                }
                companyTagStats
                codeSnippets {
                    lang
                    langSlug
                    code
                    __typename
                }
                stats
                hints
                solution {
                    id
                    canSeeDetail
                    paidOnly
                    __typename
                }
                status
                sampleTestCase
                metaData
                judgerAvailable
                judgeType
                mysqlSchemas
                enableRunCode
                enableTestMode
                enableDebugger
                envInfo
                libraryUrl
                questionDetailUrl
                __typename
            }
        }
        """
        
        variables = {"titleSlug": title_slug}
        
        try:
            response = self.session.post(
                "https://leetcode.com/graphql/",
                json={"query": query, "variables": variables},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]["question"]:
                    return data["data"]["question"]
        except Exception as e:
            print(f"⚠️  Failed to fetch details for {title_slug}: {e}")
        
        return {}
    
    def export_to_csv(self, output_file: str = "data/historical.csv", limit: int = 1000):
        """Export all data to CSV format"""
        print(f"🔄 Fetching up to {limit} submissions...")
        submissions = self.fetch_all_submissions(limit)
        print(f"✅ Found {len(submissions)} submissions")
        
        # Get unique problems (deduplicate by title)
        unique_problems = {}
        for sub in submissions:
            if sub["title"] not in unique_problems:
                unique_problems[sub["title"]] = sub
        
        print(f"📊 Processing {len(unique_problems)} unique problems...")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['leetcode_number', 'title', 'difficulty', 'solved_date', 'attempts', 'topics'])
            
            for i, (title, sub) in enumerate(unique_problems.items(), 1):
                if i % 10 == 0:
                    print(f"   Processed {i}/{len(unique_problems)} problems...")
                
                # Fetch detailed problem info
                problem_details = self.fetch_problem_details(sub["titleSlug"])
                
                # Extract data
                leetcode_number = problem_details.get("questionFrontendId", "Unknown")
                difficulty = problem_details.get("difficulty", "Unknown").lower()
                solved_date = datetime.fromtimestamp(sub["timestamp"]).strftime("%Y-%m-%d")
                attempts = 1  # We don't have attempt count from submissions API
                
                # Extract topics
                topics = []
                if "topicTags" in problem_details:
                    topics = [tag["name"] for tag in problem_details["topicTags"]]
                topics_str = "|".join(topics) if topics else "Unknown"
                
                writer.writerow([
                    leetcode_number,
                    title,
                    difficulty,
                    solved_date,
                    attempts,
                    topics_str
                ])
        
        print(f"✅ Exported {len(unique_problems)} problems to {output_file}")

if __name__ == "__main__":
    exporter = LeetCodeExporter()
    exporter.export_to_csv(limit=1000)  # Adjust limit as needed

