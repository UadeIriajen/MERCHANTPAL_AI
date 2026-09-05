"""LLM-based implementation of the AI step — a real understanding of
free-form speech, using Claude, in place of the regex heuristics in
transcript_parser.py. Requires ANTHROPIC_API_KEY (see .env.example).

Same contract as parse_transcript(): str in, ParsedTransaction out. Falls
back to the rule-based parser automatically if no key is configured or the
API call fails for any reason, so the pipeline keeps working either way —
callers don't need to know which path ran.
"""

import logging
from decimal import Decimal

from pydantic import BaseModel

from src.models.transaction import TransactionType
from src.services.transcript_parser import ParsedTransaction, parse_transcript

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You turn a shopkeeper's spoken note into a structured transaction "
    "record. Classify it as a sale (money coming in from a customer), a "
    "purchase (restocking inventory from a supplier), or an expense (a cost "
    "with no goods received, e.g. rent, fuel, transport). Extract the item/"
    "description, quantity (default 1 if not stated), the total amount as a "
    "plain number, and the counterparty (customer/supplier name, or \"N/A\" "
    "for an expense). Set matched=false only if you cannot find any amount "
    "at all."
)


class _LLMTransaction(BaseModel):
    type: TransactionType
    item: str
    quantity: int
    total: float
    counterparty: str
    matched: bool


def parse_transcript_with_llm(transcript: str) -> ParsedTransaction:
    try:
        from anthropic import Anthropic

        client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        response = client.messages.parse(
            model="claude-opus-5",
            max_tokens=2000,
            output_config={"effort": "low"},  # simple extraction, keep it cheap
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": transcript}],
            output_format=_LLMTransaction,
        )
        parsed = response.parsed_output
        return ParsedTransaction(
            type=parsed.type,
            item=parsed.item,
            quantity=parsed.quantity,
            total=Decimal(str(parsed.total)),
            counterparty=parsed.counterparty,
            matched=parsed.matched,
        )
    except Exception:
        logger.warning(
            "LLM transcript parsing unavailable, falling back to the rule-based parser",
            exc_info=True,
        )
        return parse_transcript(transcript)
