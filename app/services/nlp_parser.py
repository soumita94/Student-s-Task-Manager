from __future__ import annotations

from datetime import datetime, timezone
import json
import time

from openai import APIStatusError, OpenAI
from pydantic import ValidationError

from app.config import settings
from app.schemas import TaskCreate


def _create_completion_with_retry(
    client: OpenAI,
    model_name: str,
    system_prompt: str,
    command: str,
) -> str:
    retryable_status_codes = {429, 500, 502, 503, 504}
    max_attempts = 4

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model=model_name,
                response_format={"type": "json_object"},
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt.strip()},
                    {"role": "user", "content": command},
                ],
            )
            return response.choices[0].message.content or "{}"
        except APIStatusError as exc:
            should_retry = exc.status_code in retryable_status_codes and attempt < max_attempts
            if not should_retry:
                raise
            # Exponential backoff for transient provider overload.
            time.sleep(2 ** (attempt - 1))

    return "{}"


def parse_nlp_command_to_task(command: str) -> TaskCreate:
    """
    Parse natural language task commands into a validated TaskCreate payload.
    """
    llm_provider = settings.llm_provider.strip().lower()
    if llm_provider == "gemini":
        api_key = settings.google_api_key
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set.")
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        model_name = settings.gemini_model
    else:
        api_key = settings.openai_api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        client = OpenAI(api_key=api_key)
        model_name = settings.openai_model

    now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    system_prompt = f"""
You convert student task commands into STRICT JSON for TaskCreate.
Current UTC time: {now_utc}

Return ONLY valid JSON with exactly these keys:
- title (string)
- description (string or null)
- kind ("rigid" | "flexible")
- deadline_at (ISO 8601 UTC string, must end with "Z")
- category_weight (float, 0.1 to 10.0)
- importance (int, 1 to 10)
- estimated_minutes (int >= 1 or null)
- actual_time_taken (int >= 1 or null; usually null for new tasks)

Rules:
1) Parse relative deadlines ("next Tuesday 3 PM", "tomorrow evening") against current UTC time.
2) If user gives duration in hours/minutes, convert to estimated_minutes.
3) If duration is not given, use null.
4) Map task type to category_weight using this rubric:
   - high-stakes exam/prep/submission-critical tasks: 1.5 to 2.2
   - graded assignments/projects/labs: 1.2 to 1.6
   - regular practice/revision/reading: 0.8 to 1.2
   - optional/low-impact tasks: 0.4 to 0.8
5) Set kind:
   - rigid: explicit hard deadline/time
   - flexible: no strict date-time or routine practice
6) Keep title concise and actionable.
7) If text is ambiguous, choose safe defaults:
   - importance: 5
   - category_weight: 1.0
   - kind: flexible
   - deadline_at: now + 3 days, same hour, in UTC.
"""

    content = _create_completion_with_retry(client, model_name, system_prompt, command)
    payload = json.loads(content)
    try:
        return TaskCreate.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"LLM output failed TaskCreate validation: {exc}") from exc

