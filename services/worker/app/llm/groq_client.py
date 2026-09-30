import logging

from groq import Groq

from pr_review_shared.config import settings

logger = logging.getLogger(__name__)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
    return _client


def complete_json(system_prompt: str, user_prompt: str, *, temperature: float = 0.2) -> str:
    """Calls Groq's chat completions API in JSON mode and returns the raw JSON string.
    Raises on transport/API errors so Temporal's activity RetryPolicy can back off and retry."""
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.groq_model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or "{}"
