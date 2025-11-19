import base64
import time
import tempfile
import os
from typing import Optional
from openai import OpenAI

from models.speech import SpeechTranscription, SpeechModel, VoiceCommand
from config import get_settings


class WhisperProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = "whisper-1"
    
    def transcribe_audio(self, audio_data: str, language: str = "en") -> SpeechTranscription:
        """
        Transcribe audio using OpenAI Whisper.
        
        Args:
            audio_data: Base64 encoded audio string
            language: Language code (default: en)
            
        Returns:
            SpeechTranscription with transcribed text and metadata
        """
        start_time = time.time()
        
        try:
            # Decode base64 audio and save to temp file
            audio_bytes = base64.b64decode(audio_data)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name
            
            try:
                # Call Whisper API
                with open(temp_audio_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language,
                        response_format="verbose_json"
                    )
                
                processing_time = (time.time() - start_time) * 1000
                
                # Extract transcription and confidence
                text = response.text
                
                # Whisper doesn't provide word-level confidence, estimate from response
                confidence = self._estimate_confidence(response)
                
                return SpeechTranscription(
                    text=text,
                    confidence=confidence,
                    language=language,
                    model_used=SpeechModel.WHISPER,
                    processing_time_ms=processing_time
                )
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    
        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")
    
    def process_voice_command(self, audio_data: str, language: str = "en") -> VoiceCommand:
        """
        Process voice command: transcribe and extract intent/entities.
        """
        # First transcribe
        transcription = self.transcribe_audio(audio_data, language)
        
        # Extract intent and entities using LLM
        intent_analysis = self._analyze_intent(transcription.text)
        
        return VoiceCommand(
            transcription=transcription,
            intent=intent_analysis["intent"],
            entities=intent_analysis["entities"],
            confidence=intent_analysis["confidence"],
            requires_clarification=intent_analysis["requires_clarification"],
            clarification_questions=intent_analysis.get("clarification_questions", [])
        )
    
    def _estimate_confidence(self, response) -> float:
        """
        Estimate confidence score from Whisper response.
        Whisper doesn't provide explicit confidence, so we use heuristics.
        """
        # Default confidence
        confidence = 0.85
        
        # Adjust based on text length and coherence
        text = response.text
        if len(text) < 5:
            confidence = 0.6
        elif len(text) > 100:
            confidence = 0.9
        
        return confidence
    
    def _analyze_intent(self, text: str) -> dict:
        """
        Analyze intent and extract entities from transcribed text using LLM.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an intent classifier for an e-commerce voice assistant.
                        Analyze the user's voice command and extract:
                        1. Intent: search, compare, purchase, question, recommendation, price_check, availability_check, review_analysis
                        2. Entities: product names, brands, colors, price ranges, features
                        3. Confidence: how confident you are (0-1)
                        4. Whether clarification is needed
                        5. Clarification questions if needed
                        
                        Respond in JSON format:
                        {
                          "intent": "intent_type",
                          "entities": {"key": "value"},
                          "confidence": 0.0-1.0,
                          "requires_clarification": true/false,
                          "clarification_questions": ["question1", "question2"]
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this voice command: {text}"
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            # Fallback if intent analysis fails
            return {
                "intent": "search",
                "entities": {"query": text},
                "confidence": 0.5,
                "requires_clarification": False,
                "clarification_questions": []
            }
    
    def validate_audio(self, audio_data: str) -> bool:
        """Validate audio data before processing."""
        try:
            audio_bytes = base64.b64decode(audio_data)
            
            # Check audio size (max 25MB for Whisper)
            if len(audio_bytes) > 25 * 1024 * 1024:
                raise ValueError("Audio size exceeds 25MB limit")
            
            # Check minimum size
            if len(audio_bytes) < 1000:
                raise ValueError("Audio file too small")
            
            return True
            
        except Exception as e:
            raise ValueError(f"Invalid audio data: {str(e)}")
