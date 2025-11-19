from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class SpeechModel(str, Enum):
    WHISPER = "whisper-1"
    DEEPGRAM = "deepgram-nova-2"


class SpeechTranscription(BaseModel):
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., ge=0, le=1)
    language: str = Field(default="en")
    model_used: SpeechModel
    processing_time_ms: float
    word_error_rate: Optional[float] = Field(None, ge=0, le=1)


class VoiceCommand(BaseModel):
    transcription: SpeechTranscription
    intent: str = Field(..., description="Classified intent from voice")
    entities: dict = Field(default_factory=dict, description="Extracted entities")
    confidence: float = Field(..., ge=0, le=1)
    requires_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)
