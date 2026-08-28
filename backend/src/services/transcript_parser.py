"""The "AI" step of Voice -> AI -> Transaction -> Database.

This is a deliberately simple, dependency-free, rule-based parser — no API
key, no model download, works offline. It exists so the pipeline is fully
wired end-to-end today. Swap it out later by giving `parse_transcript` the
same signature (str in, ParsedTransaction out) but implementing it with a
real LLM call (e.g. the Anthropic or OpenAI SDK) or a proper NLU model —
nothing else in the pipeline needs to change.

Coverage is intentionally narrow: "<verb> [<qty> <unit> of] <item> to/from
<Name> for <amount>", e.g. the example already in the frontend's Clarify
screen: "Sold two plates of jollof and a chicken to Kunle for twelve
thousand." It will not understand arbitrary free-form speech — that's what
a real model buys you later.
"""

import re
from dataclasses import dataclass
from decimal import Decimal

from src.models.transaction import TransactionType

_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
_MULTIPLIERS = {"hundred": 100, "thousand": 1_000, "million": 1_000_000}

_PURCHASE_KEYWORDS = ("bought", "purchased", "restocked")
_EXPENSE_KEYWORDS = ("spent", "paid", "expense", "bill")


def _words_to_number(words: list[str]) -> int | None:
    """Convert a leading run of English number-words to an int, e.g.
    ["twelve", "thousand"] -> 12000. Stops at the first word it can't use."""
    total = 0
    current = 0
    found = False
    for word in words:
        word = word.lower()
        if word in _ONES:
            current += _ONES[word]
            found = True
        elif word in _TENS:
            current += _TENS[word]
            found = True
        elif word == "hundred":
            current = (current or 1) * 100
            found = True
        elif word in ("thousand", "million"):
            total += (current or 1) * _MULTIPLIERS[word]
            current = 0
            found = True
        elif word == "and":
            continue
        else:
            break
    total += current
    return total if found else None


def _extract_amount(text: str, transaction_type: TransactionType) -> Decimal | None:
    lower = text.lower()
    if transaction_type == TransactionType.EXPENSE:
        # Expenses read "<verb> <amount> on/for <item>" — amount comes
        # right after the verb, ahead of on/for, not after it.
        match = re.search(r"\b(?:paid|spent)\s+(.+?)\s+(?:on|for)\b", lower)
    else:
        # Sales/purchases read "... for <amount>" — amount trails a
        # price-introducing keyword.
        match = re.search(r"(?:for|worth|totaling|totalling|costing)\s+(.+?)[.!?]?$", lower)
    candidate = match.group(1) if match else lower

    digit_match = re.search(r"[\d][\d,]*(?:\.\d+)?", candidate)
    if digit_match:
        return Decimal(digit_match.group(0).replace(",", ""))

    words = re.findall(r"[a-zA-Z]+", candidate)
    number = _words_to_number(words)
    if number is not None:
        return Decimal(number)

    # Last resort: any digits anywhere in the transcript.
    digit_match = re.search(r"[\d][\d,]*(?:\.\d+)?", lower)
    if digit_match:
        return Decimal(digit_match.group(0).replace(",", ""))
    return None


def _extract_counterparty(text: str, transaction_type: TransactionType) -> str:
    keyword = "from" if transaction_type == TransactionType.PURCHASE else "to"
    match = re.search(rf"\b{keyword}\s+([A-Z][\w'-]*(?:\s+[A-Z][\w'-]*)*)", text)
    if match:
        return match.group(1)
    defaults = {
        TransactionType.SALE: "Walk-in customer",
        TransactionType.PURCHASE: "Unknown supplier",
        TransactionType.EXPENSE: "N/A",
    }
    return defaults[transaction_type]


def _extract_item_and_quantity(text: str, transaction_type: TransactionType) -> tuple[str, int]:
    lower = text.lower()

    # Expenses read "<verb> <amount> on/for <item>" — the item comes after
    # the price, not before it, so it needs its own pattern.
    if transaction_type == TransactionType.EXPENSE:
        match = re.search(r"\b(?:on|for)\s+(.+?)[.!?]?$", lower)
        if match:
            return match.group(1).strip(), 1
        return text.strip(), 1

    # "<qty> <unit> of <item>" — e.g. "two plates of jollof rice"
    match = re.search(
        r"\b(\d+|" + "|".join(_ONES) + r")\s+[a-z]+s?\s+of\s+(.+?)"
        r"(?=\s+(?:to|from|for|and)\b|[.!?]|$)",
        lower,
    )
    if match:
        qty_word, item = match.group(1), match.group(2).strip()
        quantity = int(qty_word) if qty_word.isdigit() else _ONES.get(qty_word, 1)
        return item, quantity

    # Fallback: whatever sits between the leading verb and to/from/for.
    match = re.search(
        r"\b(?:sold|bought|purchased)\s+(.+?)"
        r"(?=\s+(?:to|from|for)\b|[.!?]|$)",
        lower,
    )
    if match:
        return match.group(1).strip(), 1

    return text.strip(), 1


def _classify_type(lower: str) -> TransactionType:
    if any(keyword in lower for keyword in _PURCHASE_KEYWORDS):
        return TransactionType.PURCHASE
    if any(keyword in lower for keyword in _EXPENSE_KEYWORDS) and "sold" not in lower:
        return TransactionType.EXPENSE
    return TransactionType.SALE


@dataclass
class ParsedTransaction:
    type: TransactionType
    item: str
    quantity: int
    total: Decimal
    counterparty: str
    matched: bool  # False if we couldn't confidently find an amount — surface for review


def parse_transcript(transcript: str) -> ParsedTransaction:
    lower = transcript.lower()
    transaction_type = _classify_type(lower)
    amount = _extract_amount(transcript, transaction_type)
    counterparty = _extract_counterparty(transcript, transaction_type)
    item, quantity = _extract_item_and_quantity(transcript, transaction_type)

    return ParsedTransaction(
        type=transaction_type,
        item=item.title() if item else "Untitled",
        quantity=quantity,
        total=amount if amount is not None else Decimal(0),
        counterparty=counterparty,
        matched=amount is not None,
    )
