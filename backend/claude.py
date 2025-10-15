import json
import os
from typing import Dict, List, Optional
import requests

from dotenv import load_dotenv

try:
    import anthropic  # type: ignore
    # Newer SDK
    try:
        from anthropic import Anthropic  # type: ignore
    except Exception:
        Anthropic = None  # type: ignore
    # Legacy SDK (<=0.7)
    try:
        from anthropic import Client  # type: ignore
    except Exception:
        Client = None  # type: ignore
except Exception:
    anthropic = None  # type: ignore
    Anthropic = None  # type: ignore
    Client = None  # type: ignore


class ClaudeClient:
    """Thin wrapper around Anthropic Claude for generating daily plans."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        load_dotenv()
        # Support both ANTHROPIC_API_KEY and ANTHROPIC_SECRET
        key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_SECRET")
        if not key:
            raise RuntimeError("Anthropic API key not set. Configure ANTHROPIC_API_KEY or ANTHROPIC_SECRET in environment.")

        # Ensure env var is available for SDKs that read from env and for HTTP fallback
        os.environ.setdefault("ANTHROPIC_API_KEY", key)
        self.api_key = key

        self.client = None
        if anthropic is not None:
            # Try to initialize SDK; it's okay if it fails, we'll use HTTP fallback
            if Anthropic is not None:
                try:
                    self.client = Anthropic()  # type: ignore
                except Exception:
                    self.client = None
            if self.client is None and Client is not None:
                try:
                    self.client = Client()  # type: ignore
                except Exception:
                    self.client = None
        # Prefer modern model; provide legacy fallback used by old SDKs
        self.model = model or "claude-sonnet-4-5-20250929"
        self.legacy_model = "claude-2"

    def generate_daily_plan(
        self,
        topic_stats: List[Dict],
        time_minutes: int,
        custom_instructions: Optional[str] = None,
    ) -> Dict:
        prompt = self._build_prompt(topic_stats, time_minutes, custom_instructions)

        # Three code paths: modern SDK, legacy SDK, or direct HTTP
        content_text = "{}"
        if self.client is not None and hasattr(self.client, "messages"):
            try:
                response = self.client.messages.create(  # type: ignore
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                content_text = response.content[0].text if response and getattr(response, "content", None) else "{}"
            except Exception:
                content_text = "{}"
        elif self.client is not None and hasattr(self.client, "completions"):
            try:
                hp = getattr(anthropic, "HUMAN_PROMPT", "\n\nHuman:")
                ap = getattr(anthropic, "AI_PROMPT", "\n\nAssistant:")
                legacy_prompt = f"{hp} {prompt}{ap}"
                response = self.client.completions.create(  # type: ignore
                    model=self.legacy_model,
                    max_tokens_to_sample=2000,
                    prompt=legacy_prompt,
                )
                content_text = getattr(response, "completion", "{}")
            except Exception:
                content_text = "{}"
        else:
            # HTTP fallback to Messages API
            try:
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                body = {
                    "model": self.model,
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                }
                r = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
                r.raise_for_status()
                j = r.json()
                parts = j.get("content") or []
                if isinstance(parts, list) and parts:
                    content_text = parts[0].get("text", "{}")
                else:
                    content_text = "{}"
            except Exception as e:
                # Let parser fallback handle an empty body
                content_text = "{}"

        # Parse expected JSON response
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


