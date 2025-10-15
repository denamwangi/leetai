import json
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

try:
    import anthropic
except Exception:  # library may not be installed in some environments yet
    anthropic = None  # type: ignore


class ClaudeClient:
    """Thin wrapper around Anthropic Claude for generating daily plans."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        load_dotenv()
        # Support both ANTHROPIC_API_KEY and ANTHROPIC_SECRET
        key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_SECRET")
        if not key:
            raise RuntimeError("Anthropic API key not set. Configure ANTHROPIC_API_KEY or ANTHROPIC_SECRET in environment.")

        if anthropic is None:
            raise RuntimeError("anthropic package not installed. Add it to requirements and install.")

        self.client = anthropic.Anthropic(api_key=key)
        # Use plan's suggested model string; allow override
        self.model = model or "claude-sonnet-4-5-20250929"

    def generate_daily_plan(
        self,
        topic_stats: List[Dict],
        time_minutes: int,
        custom_instructions: Optional[str] = None,
    ) -> Dict:
        prompt = self._build_prompt(topic_stats, time_minutes, custom_instructions)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse expected JSON response
        content_text = response.content[0].text if response and response.content else "{}"
        parsed = self._parse_response(content_text)
        return parsed

    def _build_prompt(self, stats: List[Dict], time_minutes: int, custom_instructions: Optional[str]) -> str:
        return f"""
You are a LeetCode study assistant. Generate a personalized daily study plan.

AVAILABLE TIME: {time_minutes} minutes

RECENT ACTIVITY:
{self._format_stats(stats)}

REQUIREMENTS:
1. Recommend specific LeetCode problems (by number and title)
2. Include ONE new topic the user hasn't practiced recently
3. Include review problems from topics solved 7-14 days ago
4. Balance difficulty: prioritize Medium, include 1 Hard if time permits
5. Estimate 15 min for Easy, 25 min for Medium, 40 min for Hard

OUTPUT FORMAT (JSON):
{{
  "focus_topic": "topic name",
  "recommendations": [
    {{"leetcode_number": 123, "title": "Problem", "difficulty": "medium",
      "reason": "...", "estimated_minutes": 25}}
  ],
  "rationale": "explanation..."
}}

{f"ADDITIONAL: {custom_instructions}" if custom_instructions else ""}
"""

    def _format_stats(self, stats: List[Dict]) -> str:
        # Keep this simple; Claude doesn't need the full raw dataset
        lines: List[str] = []
        for s in stats[:30]:  # cap for prompt length
            lines.append(
                f"- {s.get('topic')}: score={s.get('weighted_score')}, last={s.get('last_solved_date')}"
            )
        return "\n".join(lines)

    def _parse_response(self, text: str) -> Dict:
        # Attempt direct JSON parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # Try to extract JSON block from text
        start = text.find("{")
        end = text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass

        # Fallback minimal structure to avoid crashing callers
        return {
            "focus_topic": "General Review",
            "recommendations": [],
            "rationale": "Failed to parse structured response; please retry.",
        }


