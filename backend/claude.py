import json
import logging
import os
from typing import Dict, List, Optional
import requests

from dotenv import load_dotenv
from backend.observability import start_trace, start_span, end_span

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



    # Phase 7: Two-step generation helpers
    def generate_topics_decision(self, stats: List[Dict], time_minutes: int, custom_instructions: Optional[str]) -> Dict:
        """Prompt 1: Decide topics using llm_prompts; return {new_topic, review_topics}."""
        # Lazy import to avoid circular
        from backend.llm_prompts import build_prompt1_topic_decision

        prompt = build_prompt1_topic_decision(stats, time_minutes, custom_instructions)
        logging.info(f"🤖 LLM Prompt for topics decision:\n{prompt}")
        
        trace = start_trace("claude.generate_topics_decision", metadata={"model": self.model, "time_minutes": time_minutes})
        call_span = start_span(trace, name="anthropic.messages", input={"prompt_preview": str(prompt)[:500], "model": self.model})
        content_text = "{}"
        try:
            if self.client is not None and hasattr(self.client, "messages"):
                response = self.client.messages.create(  # type: ignore
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                content_text = response.content[0].text if response and getattr(response, "content", None) else "{}"
            elif self.client is not None and hasattr(self.client, "completions"):
                hp = getattr(anthropic, "HUMAN_PROMPT", "\n\nHuman:")
                ap = getattr(anthropic, "AI_PROMPT", "\n\nAssistant:")
                legacy_prompt = f"{hp} {prompt}{ap}"
                response = self.client.completions.create(  # type: ignore
                    model=self.legacy_model,
                    max_tokens_to_sample=2000,
                    prompt=legacy_prompt,
                )
                content_text = getattr(response, "completion", "{}")
            else:
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
            # Fallback to empty; parser will handle defaults
            content_text = "{}"
            end_span(call_span, output={"error": str(e)}, level="ERROR")
        else:
            end_span(call_span, output={"preview": str(content_text)[:500]})
        
        logging.info(f"🤖 LLM Response for topics decision:\n{content_text}")
        
        parsed = self._parse_response(content_text)
        logging.info(f"🤖 Parsed topics decision: {parsed}")
        
        # Ensure keys exist
        if "new_topic" not in parsed or not isinstance(parsed.get("review_topics"), list):
            fallback = {"new_topic": "Arrays", "review_topics": ["Two Pointers"]}
            logging.warning(f"🤖 Using fallback topics decision: {fallback}")
            return fallback
        return parsed

    def generate_daily_plan_from_problems(
        self,
        topic_decision: Dict,
        problems: List[Dict],
        time_minutes: int,
        custom_instructions: Optional[str],
    ) -> Dict:
        """Prompt 2: Build plan from given problems and topic decision using llm_prompts."""
        from backend.llm_prompts import build_prompt2_daily_plan

        prompt = build_prompt2_daily_plan(topic_decision, problems, time_minutes, custom_instructions)
        logging.info(f"🤖 LLM Prompt for daily plan:\n{prompt}")
        
        if os.getenv("CLAUDE_DEBUG"):
            # Print full prompt for debugging
            print("[CLAUDE DEBUG] Prompt2 FULL:\n" + (prompt if isinstance(prompt, str) else str(prompt)))
        trace = start_trace("claude.generate_daily_plan_from_problems", metadata={"model": self.model, "time_minutes": time_minutes})
        call_span = start_span(trace, name="anthropic.messages", input={"prompt_preview": str(prompt)[:500], "model": self.model})
        content_text = "{}"
        try:
            if self.client is not None and hasattr(self.client, "messages"):
                response = self.client.messages.create(  # type: ignore
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                content_text = response.content[0].text if response and getattr(response, "content", None) else "{}"
            elif self.client is not None and hasattr(self.client, "completions"):
                hp = getattr(anthropic, "HUMAN_PROMPT", "\n\nHuman:")
                ap = getattr(anthropic, "AI_PROMPT", "\n\nAssistant:")
                legacy_prompt = f"{hp} {prompt}{ap}"
                response = self.client.completions.create(  # type: ignore
                    model=self.legacy_model,
                    max_tokens_to_sample=2000,
                    prompt=legacy_prompt,
                )
                content_text = getattr(response, "completion", "{}")
            else:
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
        except Exception:
            content_text = "{}"
            end_span(call_span, output={"error": "anthropic call failed"}, level="ERROR")
        else:
            end_span(call_span, output={"preview": str(content_text)[:500]})
        
        logging.info(f"🤖 LLM Response for daily plan:\n{content_text}")
        
        if os.getenv("CLAUDE_DEBUG"):
            print("[CLAUDE DEBUG] Raw2:\n" + str(content_text)[:2000])
        parsed = self._parse_response(content_text)
        logging.info(f"🤖 Parsed daily plan: {parsed}")
        # Ensure required keys
        # Ensure required keys (old plan schema)
        if "recommendations" not in parsed or not isinstance(parsed.get("recommendations"), list):
            parsed["recommendations"] = []
        if "focus_topic" not in parsed:
            parsed["focus_topic"] = topic_decision.get("new_topic") or "General Review"
        for rec in parsed["recommendations"]:
            rec.setdefault("estimated_minutes", 25)
            if not rec.get("leetcode_url") and rec.get("title"):
                slug = (rec["title"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "").replace(".", "").replace("'", ""))
                rec["leetcode_url"] = f"https://leetcode.com/problems/{slug}/description/"
        return parsed


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


