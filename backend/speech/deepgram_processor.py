import base64
import time
from typing import Optional

try:
    from deepgram import DeepgramClient, PrerecordedOptions
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False

from models.speech import SpeechTranscription, SpeechModel
from config import get_settings


class DeepgramProcessor:
    def __init__(self):
        if not DEEPGRAM_AVAILABLE:
            raise ImportError("Deepgram SDK not installed. Install with: pip install deepgram-sdk")
        
        self.settings = get_settings()
        if not self.settings.deepgram_api_key:
            raise ValueError("DEEPGRAM_API_KEY not configured")
        
        self.client = DeepgramClient(self.settings.deepgram_api_key)
        self.model = "nova-2"
    
    def transcribe_audio(self, audio_data: str, language: str = "en") -> SpeechTranscription:
        """
        Transcribe audio using Deepgram Nova 2.
        
        Args:
            audio_data: Base64 encoded audio string
            language: Language code (default: en)
            
        Returns:
            SpeechTranscription with transcribed text and metadata
        """
        start_time = time.time()
        
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Configure transcription options
            options = PrerecordedOptions(
                model=self.model,
                language=language,
                smart_format=True,
                punctuate=True,
                diarize=False,
                utterances=False
            )
            
            # Call Deepgram API
            response = self.client.listen.prerecorded.v("1").transcribe_file(
                {"buffer": audio_bytes},
                options
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Extract transcription and confidence
            result = response.results.channels[0].alternatives[0]
            text = result.transcript
            confidence = result.confidence
            
            return SpeechTranscription(
                text=text,
                confidence=confidence,
                language=language,
                model_used=SpeechModel.DEEPGRAM,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            raise Exception(f"Deepgram transcription failed: {str(e)}")
    
    def validate_audio(self, audio_data: str) -> bool:
        """Validate audio data before processing."""
        try:
            audio_bytes = base64.b64decode(audio_data)
            
            # Check minimum size
            if len(audio_bytes) < 1000:
                raise ValueError("Audio file too small")
            
            return True
            
        except Exception as e:
            raise ValueError(f"Invalid audio data: {str(e)}")
