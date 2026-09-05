from typing import Any

from pydantic import BaseModel


class AssistantQuestionRequest(BaseModel):
    question: str


class AssistantAnswerResponse(BaseModel):
    question: str
    intent: str
    supported: bool
    explanation: str
    facts: dict[str, Any]