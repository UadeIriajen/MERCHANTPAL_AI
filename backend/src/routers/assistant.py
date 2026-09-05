from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth import get_current_user, scope_id
from src.dependencies import get_db
from src.schemas.assistant import VoiceInterpretRequest, VoiceInterpretResponse
from src.schemas.assistant_questions import AssistantAnswerResponse, AssistantQuestionRequest
from src.schemas.transaction import TransactionCreate
from src.services.business_analytics import answer_question
from src.services.business_explainer import explain_business_facts
from src.services.llm_transcript_parser import parse_transcript_with_llm

router = APIRouter(prefix="/assistant", tags=["assistant"], dependencies=[Depends(get_current_user)])


@router.post("/answer", response_model=AssistantAnswerResponse)
def answer_business_question(
    payload: AssistantQuestionRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> AssistantAnswerResponse:
    intent, facts = answer_question(db, payload.question, scope_id(current_user))
    if intent is None:
        return AssistantAnswerResponse(
            question=payload.question,
            intent="unsupported",
            supported=False,
            explanation="I can answer what you made today, what you spent this week, your best-selling product, and what to restock.",
            facts={},
        )

    if intent == "daily_earnings":
        explanation = f"You made {facts['amount']} today."
    elif intent == "weekly_spend":
        explanation = f"You spent {facts['total_spend']} this week."
    elif intent == "best_selling":
        result = facts["result"]
        explanation = "You do not have any recorded sales yet." if result is None else f"{result['product']} is your best-selling product with {result['quantity']} units sold."
    else:
        items = facts["items"]
        explanation = "Nothing is below the restock threshold right now." if not items else "You should restock " + ", ".join(item["product"] for item in items) + "."

    return AssistantAnswerResponse(
        question=payload.question,
        intent=intent,
        supported=True,
        explanation=explain_business_facts(payload.question, intent, facts, explanation),
        facts=facts,
    )


@router.post("/interpret", response_model=VoiceInterpretResponse)
def interpret_voice_note(payload: VoiceInterpretRequest) -> VoiceInterpretResponse:
    """The AI step: transcript in, a draft transaction out. This does NOT
    save anything — it matches the frontend's Clarify screen, which shows
    the interpretation for the merchant to confirm or edit before it's
    actually recorded via POST /transactions.

    Uses Claude to understand the transcript when ANTHROPIC_API_KEY is set
    (see .env.example); otherwise falls back automatically to the
    dependency-free rule-based parser in transcript_parser.py, so this
    endpoint works either way.

    `transcript` stands in for real speech-to-text output. The frontend's
    voice recorder doesn't capture real audio yet either — once both sides
    are ready, add an audio-upload variant of this endpoint that runs a
    real STT provider and feeds its output into the same parser.
    """
    parsed = parse_transcript_with_llm(payload.transcript)
    draft = TransactionCreate(
        type=parsed.type,
        item=parsed.item,
        quantity=parsed.quantity,
        total=parsed.total,
        counterparty=parsed.counterparty,
        source_transcript=payload.transcript,
    )
    return VoiceInterpretResponse(transcript=payload.transcript, matched=parsed.matched, draft=draft)
