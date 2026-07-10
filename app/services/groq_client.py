"""
Groq API client setup.
Wraps the Groq SDK into a simple, reusable client object.
"""

from groq import Groq

from app.config.settings import GROQ_API_KEY, GROQ_MODEL


# ── Client instance (module-level singleton) ──────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)


def chat_completion(messages: list[dict]) -> str:
    """
    Send a list of messages to the Groq chat completions endpoint
    and return the AI's reply as a plain string.

    Args:
        messages: A list of dicts following the OpenAI message format:
                  [{"role": "system"|"user"|"assistant", "content": "..."}]

    Returns:
        The AI's text reply.
    """
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content


def chat_completion_json(messages: list[dict]) -> dict:
    """
    Send a list of messages to the Groq chat completions endpoint
    with JSON response format, returning the parsed dict.
    """
    import json
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

