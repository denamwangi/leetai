from typing import Dict, List, Optional


def build_prompt1_topic_decision(
    stats: List[Dict],
    time_minutes: int,
    custom_instructions: Optional[str],
) -> str:
    # Format stats for better LLM readability
    formatted_stats = []
    for stat in stats:
        topic_name = stat.get("topic", "Unknown")
        last_solved = stat.get("last_solved_date")
        weighted_score = stat.get("weighted_score", 0.0)
        
        # Create a summary of recent activity
        recent_summary = {
            "topic": topic_name,
            "last_solved": str(last_solved) if last_solved else "never",
            "recent_activity": {
                "3d": f"{stat.get('easy_3d', 0)}E/{stat.get('medium_3d', 0)}M/{stat.get('hard_3d', 0)}H",
                "7d": f"{stat.get('easy_7d', 0)}E/{stat.get('medium_7d', 0)}M/{stat.get('hard_7d', 0)}H",
                "14d": f"{stat.get('easy_14d', 0)}E/{stat.get('medium_14d', 0)}M/{stat.get('hard_14d', 0)}H"
            },
            "weighted_score": weighted_score
        }
        formatted_stats.append(recent_summary)
    
    return f"""
    You are a LeetCode study assistant. Generate a personalized study plan for the day
    that accounts for the user's recent activity and available time. 

    1. Recommend specific LeetCode topics
    2. Include ONE new topic the user hasn't practiced recently
    3. Include up to TWO review topics from topics solved 7-14 days ago
    4. Balance difficulty: prioritize Medium, include 1 Hard if time permits
    5. Estimate 15 min for Easy, 25 min for Medium, 40 min for Hard

    OUTPUT FORMAT (JSON):
    {{
    "new_topic": "topic name",
    "review_topics": ["topic name", "topic name"],
    "rationale": "explanation..."
    }}

    Available time today: {time_minutes} minutes

    RECENT ACTIVITY:
    {formatted_stats}
    
    {f"ADDITIONAL: {custom_instructions}" if custom_instructions else ""}
    """


def build_prompt2_daily_plan(
    topic_decision: Dict,
    recent_problems: List[Dict],
    time_minutes: int,
    custom_instructions: Optional[str],
) -> str:
    return f"""
    You are a LeetCode study assistant. Generate a personalized study plan for the day
    that accounts for the user's recent activity, topics of focus, and available time. 

    1. Recommend specific LeetCode problems with their numbers and titles
    2. Fill half the time with problems for new_topic if available
    3. Fill remaining time with review_topics, prefer medium difficulty, include 1 hard if time allows
    4. Keep output predictable and machine-readable
    5. Estimate 15 min for Easy, 25 min for Medium, 40 min for Hard

    OUTPUT FORMAT (JSON):
    {{
        "recommendations": [
            {{"leetcode_number": 123, "title": "Problem", "difficulty": "medium",
              "reason": "...", "estimated_minutes": 25, "leetcode_url": "https://leetcode.com/problems/problem-slug/description/"}}
        ]
    }}

    Available time today: {time_minutes} minutes

    TOPICS OF FOCUS:
    {{
        topic_decision: {topic_decision}
    }}
    
    {f"RECENT PROBLEMS: {recent_problems}" if recent_problems else ""}
    {f"ADDITIONAL: {custom_instructions}" if custom_instructions else ""}
    """



    """
    Prompt 2: Given topic decision and recent problems, produce a concrete daily plan.
    """
    lines: List[str] = []
    lines.append("You are a LeetCode study assistant. Create a daily plan using provided problems.")
    lines.append("")
    lines.append(f"AVAILABLE TIME: {time_minutes} minutes")
    lines.append("TIME HEURISTICS: Easy=15, Medium=25, Hard=40 (unless user specifies otherwise).")
    lines.append("")
    new_topic = topic_decision.get("new_topic") or ""
    review_topics = topic_decision.get("review_topics") or []
    lines.append(f"TOPIC DECISION: new_topic={new_topic}, review_topics={review_topics}")
    lines.append("")
    # Build recent activity summary for the model
    from datetime import datetime, timedelta
    today = datetime.now().date()
    def to_date(s: str):
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            return None

    numbers = []
    for p in recent_problems:
        num = p.get('leetcode_number')
        if isinstance(num, int):
            numbers.append(num)

    def counts_in(days: int) -> Dict[str, int]:
        cutoff = today - timedelta(days=days)
        c = {"easy": 0, "medium": 0, "hard": 0}
        for p in recent_problems:
            d = to_date(str(p.get('solved_date')))
            if d and d >= cutoff:
                diff = (p.get('difficulty') or 'medium').lower()
                if diff not in c:
                    diff = 'medium'
                c[diff] += 1
        return c

    last3 = counts_in(3)
    last7 = counts_in(7)

    lines.append("RECENT_ACTIVITY:")
    lines.append("{")
    lines.append(f"  \"problem_numbers\": {numbers},")
    lines.append("  \"summary\": {")
    lines.append(f"    \"last_3d\": {{\"easy\": {last3['easy']}, \"medium\": {last3['medium']}, \"hard\": {last3['hard']}}},")
    lines.append(f"    \"last_7d\": {{\"easy\": {last7['easy']}, \"medium\": {last7['medium']}, \"hard\": {last7['hard']}}}")
    lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("REQUIREMENTS:")
    lines.append("- Include at least one recommendation for new_topic if available.")
    lines.append("- Fill remaining time with review_topics, prefer medium difficulty, include 1 hard if time allows.")
    lines.append("- Prefer problems not done in last 3–7 days when possible.")
    lines.append("- Keep output predictable and machine-readable.")
    lines.append("- Choose problems by referencing RECENT_ACTIVITY.problem_numbers only; do not invent IDs.")
    lines.append("")
    if custom_instructions:
        lines.append(f"ADDITIONAL USER INSTRUCTIONS: {custom_instructions}")
        lines.append("")
    lines.append("OUTPUT FORMAT (STRICT JSON):")
    lines.append("{" +
                 "\n  \"focus_topic\": \"<Topic>\"," +
                 "\n  \"recommendations\": [" +
                 "\n    {\"leetcode_number\": 347, \"title\": \"...\", \"difficulty\": \"medium\", " +
                 "\n     \"reason\": \"...\", \"estimated_minutes\": 25, \"leetcode_url\": \"https://leetcode.com/problems/.../description/\"}" +
                 "\n  ]," +
                 "\n  \"rationale\": \"...\"\n}")
    return "\n".join(lines)


