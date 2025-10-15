from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from database import Problem, Submission


def _get_time_windows(now: Optional[datetime] = None) -> Dict[str, datetime]:
    ref = now or datetime.now()
    return {
        "3d": ref - timedelta(days=3),
        "7d": ref - timedelta(days=7),
        "14d": ref - timedelta(days=14),
        "28d": ref - timedelta(days=28),
    }


def _which_window(solved_date: date, windows: Dict[str, datetime]) -> str:
    solved_dt = datetime.combine(solved_date, datetime.min.time())
    if solved_dt >= windows["3d"]:
        return "3d"
    if solved_dt >= windows["7d"]:
        return "7d"
    if solved_dt >= windows["14d"]:
        return "14d"
    if solved_dt >= windows["28d"]:
        return "28d"
    return "28d+"


def calculate_topic_stats(db: Session) -> List[Dict]:
    """Calculate statistics for all topics across time windows with weighted scores."""
    now = datetime.now()
    windows = _get_time_windows(now)

    # Accumulators per topic
    topic_acc: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    last_solved_by_topic: Dict[str, date] = {}

    # Fetch submissions joined with problems to get difficulty and topics
    # We iterate in Python for clarity and single-user simplicity
    submissions = (
        db.query(Submission, Problem)
        .join(Problem, Submission.problem_id == Problem.id)
        .all()
    )

    for submission, problem in submissions:
        window_key = _which_window(submission.solved_date, windows)
        difficulty = (problem.difficulty or "medium").lower()
        # Ensure difficulty in expected set
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

        for topic in (problem.topics or []):
            topic_name = topic.strip()
            if not topic_name:
                continue

            # Increment per-window, per-difficulty counters
            topic_acc[topic_name][f"{difficulty}_{'28d_plus' if window_key=='28d+' else window_key}"] += 1

            # Track last solved date
            prev = last_solved_by_topic.get(topic_name)
            if prev is None or submission.solved_date > prev:
                last_solved_by_topic[topic_name] = submission.solved_date

    # Compute weighted scores
    recency_multiplier = {"3d": 1.0, "7d": 0.8, "14d": 0.5, "28d+": 0.3}
    difficulty_weight = {"easy": 1, "medium": 2, "hard": 3}

    topic_stats: List[Dict] = []
    for topic_name, counts in topic_acc.items():
        # Build response dict matching schemas.TopicStats
        stats: Dict = {
            "topic": topic_name,
            "easy_3d": counts.get("easy_3d", 0),
            "medium_3d": counts.get("medium_3d", 0),
            "hard_3d": counts.get("hard_3d", 0),
            "easy_7d": counts.get("easy_7d", 0),
            "medium_7d": counts.get("medium_7d", 0),
            "hard_7d": counts.get("hard_7d", 0),
            "easy_14d": counts.get("easy_14d", 0),
            "medium_14d": counts.get("medium_14d", 0),
            "hard_14d": counts.get("hard_14d", 0),
            "easy_28d_plus": counts.get("easy_28d_plus", 0),
            "medium_28d_plus": counts.get("medium_28d_plus", 0),
            "hard_28d_plus": counts.get("hard_28d_plus", 0),
            "last_solved_date": last_solved_by_topic.get(topic_name),
        }

        # Weighted score across windows and difficulty
        weighted = 0.0
        for window_key, rec_mult in recency_multiplier.items():
            suffix = "28d_plus" if window_key == "28d+" else window_key
            for diff, diff_w in difficulty_weight.items():
                weighted += stats.get(f"{diff}_{suffix}", 0) * diff_w * rec_mult

        stats["weighted_score"] = round(weighted, 2)
        topic_stats.append(stats)

    # Sort topics by weighted score desc
    topic_stats.sort(key=lambda t: t.get("weighted_score", 0.0), reverse=True)
    return topic_stats


def calculate_overall_stats(db: Session) -> Dict:
    """Calculate overall statistics for the user."""
    submissions = (
        db.query(Submission, Problem)
        .join(Problem, Submission.problem_id == Problem.id)
        .all()
    )

    total_submissions = 0
    total_attempts = 0
    diff_counts = {"easy": 0, "medium": 0, "hard": 0}
    unique_topics = set()
    dates_set = set()

    for submission, problem in submissions:
        total_submissions += 1
        total_attempts += (submission.attempts or 1)
        difficulty = (problem.difficulty or "medium").lower()
        if difficulty not in diff_counts:
            difficulty = "medium"
        diff_counts[difficulty] += 1
        for topic in (problem.topics or []):
            if topic and topic.strip():
                unique_topics.add(topic.strip())
        dates_set.add(submission.solved_date)

    # Streaks based on dates_set
    current_streak, longest_streak = _compute_streaks(dates_set)

    average_attempts = round(total_attempts / total_submissions, 2) if total_submissions else 0.0

    return {
        "total_problems_solved": total_submissions,
        "total_attempts": total_attempts,
        "easy_solved": diff_counts["easy"],
        "medium_solved": diff_counts["medium"],
        "hard_solved": diff_counts["hard"],
        "unique_topics_practiced": len(unique_topics),
        "current_streak_days": current_streak,
        "longest_streak_days": longest_streak,
        "average_attempts_per_problem": average_attempts,
    }


def _compute_streaks(dates_set: set) -> Tuple[int, int]:
    if not dates_set:
        return 0, 0
    sorted_dates = sorted(dates_set)
    longest = 1
    current = 1
    # Compute longest
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current += 1
        else:
            longest = max(longest, current)
            current = 1
    longest = max(longest, current)

    # Compute current streak ending today
    today = datetime.now().date()
    streak = 0
    d = today
    while d in dates_set:
        streak += 1
        d = d - timedelta(days=1)

    return streak, longest


def get_topic_stats_by_name(db: Session, topic: str) -> Optional[Dict]:
    """Return stats for a specific topic name, or None if not present."""
    all_stats = calculate_topic_stats(db)
    for t in all_stats:
        if t.get("topic") == topic:
            return t
    return None


