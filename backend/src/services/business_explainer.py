import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def explain_business_facts(
    question: str, intent: str, facts: dict[str, Any], fallback: str
) -> str:
    """Turn verified facts into natural language without allowing recalculation."""
    try:
        from anthropic import Anthropic

        response = Anthropic().messages.create(
            model="claude-opus-5",
            max_tokens=300,
            system=(
                "Explain the business answer in plain language. Use only the supplied facts. "
                "Do not calculate, estimate, infer, or change any number. If the facts are empty, "
                "say that the records do not contain an answer. Return only the explanation."
            ),
            messages=[
                {
                    "role": "user",
                    "content": json.dumps({"question": question, "intent": intent, "facts": facts}, default=str),
                }
            ],
        )
        text = response.content[0].text.strip()
        return text or fallback
    except Exception:
        logger.debug("Business explanation unavailable; using deterministic explanation", exc_info=True)
        return fallback