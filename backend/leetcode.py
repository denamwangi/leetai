import os
from datetime import datetime
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv


class LeetCodeClient:
    """Minimal LeetCode GraphQL client for fetching recent submissions.

    This client supports authenticated requests using the LEETCODE_SESSION cookie.
    For best results, set both LEETCODE_USERNAME and LEETCODE_SESSION in your .env.
    """

    def __init__(self, username: Optional[str] = None, session_cookie: Optional[str] = None):
        load_dotenv()
        self.base_url = "https://leetcode.com/graphql"
        self.username = username or os.getenv("LEETCODE_USERNAME")
        self.session_cookie = session_cookie or os.getenv("LEETCODE_SESSION")

        self._session = requests.Session()
        if self.session_cookie:
            # LeetCode expects the cookie name to be "LEETCODE_SESSION"
            self._session.headers.update({"User-Agent": "leetcode-assistant/1.0"})
            self._session.cookies.set("LEETCODE_SESSION", self.session_cookie, domain="leetcode.com")
            print(f"🍪 Using LeetCode session cookie (length: {len(self.session_cookie)})")
        else:
            print(f"⚠️  No LEETCODE_SESSION cookie found - using public API")

    def fetch_recent_submissions(self, limit: int = 20) -> List[Dict]:
        """Fetch recent accepted submissions for the configured user.

        Returns a list of dicts with keys:
        - leetcode_number, title, difficulty, topics, leetcode_url, solved_date
        """
        if not self.username:
            # Graceful fallback when username is not provided
            print(f"⚠️  No LEETCODE_USERNAME configured. Set it in .env for best results.")
            return []

        # Step 1: Fetch recent accepted submissions (titleSlug + timestamp)
        # LeetCode public GraphQL: recentAcSubmissionList
        submissions = self._fetch_recent_ac_submissions(limit)

        # Step 2: For each titleSlug, fetch problem metadata (number, difficulty, tags)
        results: List[Dict] = []
        print(f"📊 Fetched {len(submissions)} submissions from LeetCode")
        
        for sub in submissions:
            meta = self._fetch_problem_meta(sub.get("titleSlug"))
            if not meta:
                print(f"⚠️  No metadata for {sub.get('titleSlug')}")
                continue
            # Handle leetcode_number conversion safely
            try:
                leetcode_number = int(meta["questionFrontendId"])
            except (ValueError, TypeError) as e:
                print(f"⚠️  Could not parse leetcode_number '{meta.get('questionFrontendId')}': {e}")
                continue  # Skip if we can't parse the number
            
            # Safely parse timestamp (LeetCode returns it as a string)
            raw_ts = sub.get("timestamp", 0)
            try:
                ts_int = int(raw_ts)
            except (ValueError, TypeError):
                ts_int = 0

            results.append(
                {
                    "leetcode_number": leetcode_number,
                    "title": meta["title"],
                    "difficulty": meta["difficulty"].lower(),
                    "topics": [t["name"] for t in meta.get("topicTags", [])] or ["Unknown"],
                    "leetcode_url": f"https://leetcode.com/problems/{meta['titleSlug']}/",
                    "solved_date": datetime.fromtimestamp(ts_int).date(),
                }
            )

        # De-duplicate by (leetcode_number, solved_date)
        seen = set()
        unique_results: List[Dict] = []
        for item in results:
            key = (item["leetcode_number"], item["solved_date"])
            if key in seen:
                continue
            seen.add(key)
            unique_results.append(item)

        return unique_results

    def _fetch_recent_ac_submissions(self, limit: int) -> List[Dict]:
        query = {
            "operationName": "recentAcSubmissions",
            "variables": {"username": self.username},
            "query": (
                "query recentAcSubmissions($username: String!) {\n"
                "  recentAcSubmissionList(username: $username) {\n"
                "    title\n"
                "    titleSlug\n"
                "    timestamp\n"
                "  }\n"
                "}"
            ),
        }
        try:
            resp = self._session.post(self.base_url, json=query, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            items = (data.get("data", {}) or {}).get("recentAcSubmissionList", [])
            if not isinstance(items, list):
                return []
            # Limit and map
            return items[: max(1, min(limit, 50))]
        except Exception:
            return []

    def _fetch_problem_meta(self, title_slug: Optional[str]) -> Optional[Dict]:
        if not title_slug:
            return None
        query = {
            "operationName": "questionData",
            "variables": {"titleSlug": title_slug},
            "query": (
                "query questionData($titleSlug: String!) {\n"
                "  question(titleSlug: $titleSlug) {\n"
                "    questionFrontendId\n"
                "    title\n"
                "    titleSlug\n"
                "    difficulty\n"
                "    topicTags { name }\n"
                "  }\n"
                "}"
            ),
        }
        try:
            resp = self._session.post(self.base_url, json=query, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            q = (data.get("data", {}) or {}).get("question")
            return q
        except Exception:
            return None


