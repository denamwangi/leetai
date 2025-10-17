import os
from typing import Optional, Any, Dict

from dotenv import load_dotenv

# Import Langfuse core separately from optional models to avoid false negatives
try:
    from langfuse import Langfuse  # type: ignore
except Exception:
    Langfuse = None  # type: ignore

try:
    from langfuse.model import LLMUsage  # type: ignore
except Exception:
    LLMUsage = None  # type: ignore


_langfuse_client: Optional[Any] = None


def get_langfuse() -> Optional[Any]:
    global _langfuse_client
    if _langfuse_client is not None:
        return _langfuse_client

    load_dotenv()
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not (public_key and secret_key and Langfuse):
        try:
            print(
                "[Langfuse] Skipping init: package_installed=%s, has_public=%s, has_secret=%s, host=%s"
                % (bool(Langfuse), bool(public_key), bool(secret_key), host)
            )
        except Exception:
            pass
        return None

    try:
        _langfuse_client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    except Exception as e:
        try:
            print(f"[Langfuse] Init failed: {e}")
        except Exception:
            pass
        _langfuse_client = None
    return _langfuse_client


def start_trace(name: str, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    client = get_langfuse()
    if client is None:
        return None
    try:
        return client.trace(name=name, user_id=user_id, metadata=metadata or {})
    except Exception:
        return None


def start_span(parent: Optional[Any], name: str, input: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    if parent is None:
        return None
    try:
        return parent.span(name=name, input=input, metadata=metadata or {})
    except Exception:
        return None


def end_span(span: Optional[Any], output: Optional[Any] = None, usage: Optional[Dict[str, Any]] = None, status_message: Optional[str] = None, level: str = "DEFAULT") -> None:
    if span is None:
        return
    try:
        kwargs: Dict[str, Any] = {}
        if output is not None:
            kwargs["output"] = output
        if usage and LLMUsage is not None:
            try:
                kwargs["usage"] = LLMUsage(**usage)
            except Exception:
                pass
        if status_message:
            kwargs["status_message"] = status_message
        # Only set level if it's a valid enum value
        valid_levels = {"DEFAULT", "DEBUG", "INFO", "WARNING", "ERROR"}
        if level and level in valid_levels:
            kwargs["level"] = level
        span.end(**kwargs)
    except Exception:
        pass


def observe_llm_call(trace: Optional[Any], name: str, model: str, input_text: str, call: callable) -> Dict[str, Any]:
    span = start_span(trace, name=name, input={"model": model, "input": input_text})
    try:
        result = call()
        # result should include text and possibly token counts; we pass through raw
        end_span(span, output=result)
        return {"result": result, "error": None}
    except Exception as e:
        end_span(span, output={"error": str(e)}, level="ERROR")
        raise


def langfuse_diagnostics() -> Dict[str, Any]:
    load_dotenv()
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    return {
        "package_installed": bool(Langfuse),
        "has_public_key": bool(public_key),
        "has_secret_key": bool(secret_key),
        "host": host,
    }


