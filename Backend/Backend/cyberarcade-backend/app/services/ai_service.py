"""
AI Chatbot Service — Groq (OpenAI-compatible) backend.

Provider is selected via AI_PROVIDER in .env:
  openai-compatible  (default) → Groq or any OpenAI-compatible endpoint
  ollama             → local Ollama instance (OLLAMA_BASE_URL / OLLAMA_MODEL)

Answers are SHORT by default (2-4 sentences). The model is instructed to
elaborate only when the topic genuinely requires more detail.
"""

import httpx
import openai
from uuid import UUID
from typing import Optional

from app.core.config import settings

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = (
    "You are a cybersecurity lab assistant for CyberArcade, an interactive "
    "learning platform. Your role is to guide students through lab tasks and "
    "explain cybersecurity concepts.\n\n"
    "RESPONSE STYLE:\n"
    "- Keep answers SHORT and concise — 2 to 4 sentences by default.\n"
    "- Only elaborate (step-by-step, longer explanation) when the student "
    "explicitly asks for more detail or the topic genuinely requires it.\n"
    "- Never reveal flags, expected answers, or direct solutions.\n"
    "- Explain the concept or approach, not the exact answer.\n"
    "- Use plain language; avoid unnecessary jargon unless the student uses it first.\n\n"
    "SCOPE:\n"
    "- Help with: Linux commands, networking, digital forensics, web security, "
    "tool usage (Wireshark, Nmap, Sleuth Kit, etc.), and general cybersecurity concepts.\n"
    "- Politely decline questions unrelated to cybersecurity or the current lab."
)

# Lazy singleton client — built on first request so startup never blocks.
_client: Optional[openai.AsyncOpenAI] = None


def _get_client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            timeout=httpx.Timeout(30.0, connect=10.0),
            max_retries=0,  # we handle retries / errors ourselves
        )
    return _client


async def get_chatbot_response(
    user_message: str,
    lab_id: Optional[UUID] = None,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Call the configured AI provider and return the assistant's reply.

    Raises a plain RuntimeError with a user-friendly message on failure so
    the router can return a 200 with a helpful error string instead of a 500.
    """
    client = _get_client()

    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]

    # Include recent history (last 10 turns = up to 20 messages)
    if conversation_history:
        for msg in conversation_history[-20:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model=settings.ai_model,
            messages=messages,
            max_tokens=512,
            temperature=0.5,
        )
        return response.choices[0].message.content or "No response generated."

    except openai.AuthenticationError:
        raise RuntimeError(
            "AI service authentication failed — the API key may be invalid or expired. "
            "Contact the administrator."
        )
    except openai.RateLimitError:
        raise RuntimeError(
            "The AI service is temporarily rate-limited. Please wait a moment and try again."
        )
    except openai.APITimeoutError:
        raise RuntimeError(
            "The AI service did not respond in time. Please try again."
        )
    except openai.APIConnectionError:
        raise RuntimeError(
            "Could not reach the AI service. Check your internet connection or contact the administrator."
        )
    except openai.APIStatusError as exc:
        raise RuntimeError(
            f"AI service returned an error ({exc.status_code}). Please try again later."
        )
    except Exception as exc:
        raise RuntimeError(f"Unexpected AI error: {exc}")
