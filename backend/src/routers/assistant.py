from fastapi import APIRouter

from src.schemas.assistant import VoiceInterpretRequest, VoiceInterpretResponse
from src.schemas.transaction import TransactionCreate
from src.services.llm_transcript_parser import parse_transcript_with_llm

router = APIRouter(prefix="/assistant", tags=["assistant"])


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
