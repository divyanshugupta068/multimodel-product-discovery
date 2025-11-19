import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from models.speech import SpeechTranscription, VoiceCommand
from .whisper_processor import WhisperProcessor
from config import get_settings

try:
    from .deepgram_processor import DeepgramProcessor
    DEEPGRAM_AVAILABLE = True
except:
    DEEPGRAM_AVAILABLE = False


class SpeechOrchestrator:
    """
    Orchestrates speech processing with fallback between Whisper and Deepgram.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.whisper = WhisperProcessor()
        self.deepgram = DeepgramProcessor() if DEEPGRAM_AVAILABLE and self.settings.deepgram_api_key else None
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    async def transcribe(self, audio_data: str, language: str = "en") -> SpeechTranscription:
        """
        Transcribe audio with primary model, fallback to alternative if needed.
        """
        # Try Whisper first (more reliable and available)
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.whisper.transcribe_audio,
                audio_data,
                language
            )
            return result
        except Exception as e:
            print(f"Whisper failed: {e}")
            
            # Try Deepgram as fallback
            if self.deepgram:
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        self.deepgram.transcribe_audio,
                        audio_data,
                        language
                    )
                    return result
                except Exception as e2:
                    raise Exception(f"All speech models failed. Whisper: {e}, Deepgram: {e2}")
            else:
                raise Exception(f"Whisper failed and no fallback available: {e}")
    
    async def process_voice_command(self, audio_data: str, language: str = "en") -> VoiceCommand:
        """
        Process voice command with transcription and intent extraction.
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.whisper.process_voice_command,
                audio_data,
                language
            )
            return result
        except Exception as e:
            raise Exception(f"Voice command processing failed: {str(e)}")
    
    def validate_audio(self, audio_data: str) -> bool:
        """Validate audio data."""
        return self.whisper.validate_audio(audio_data)
