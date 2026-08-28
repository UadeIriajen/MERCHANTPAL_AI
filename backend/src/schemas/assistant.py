from pydantic import BaseModel

from src.schemas.transaction import TransactionCreate


class VoiceInterpretRequest(BaseModel):
    """Input to the AI step. `transcript` stands in for real speech-to-text
    output — see src/services/transcript_parser.py for where a real STT
    provider plugs in once the frontend actually records audio."""

    transcript: str


class VoiceInterpretResponse(BaseModel):
    transcript: str
    matched: bool
    draft: TransactionCreate
