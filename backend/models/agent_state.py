from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .query import Intent, QueryType


class AgentStep(str, Enum):
    INPUT_PROCESSING = "input_processing"
    VISION_ANALYSIS = "vision_analysis"
    SPEECH_TRANSCRIPTION = "speech_transcription"
    INTENT_CLASSIFICATION = "intent_classification"
    TOOL_SELECTION = "tool_selection"
    TOOL_EXECUTION = "tool_execution"
    RESPONSE_GENERATION = "response_generation"
    COMPLETE = "complete"


class ConversationTurn(BaseModel):
    turn_id: str
    query_type: QueryType
    user_input: str
    intent: Optional[Intent] = None
    agent_response: str
    tools_used: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    current_step: AgentStep = AgentStep.INPUT_PROCESSING
    
    # Conversation history
    conversation_history: List[ConversationTurn] = Field(default_factory=list)
    
    # Current query context
    current_query: Optional[str] = None
    current_intent: Optional[Intent] = None
    
    # Intermediate results
    vision_analysis: Optional[Dict[str, Any]] = None
    speech_transcription: Optional[Dict[str, Any]] = None
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    
    # User preferences and context
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    browsing_history: List[str] = Field(default_factory=list)
    cart_items: List[str] = Field(default_factory=list)
    
    # Performance tracking
    start_time: datetime = Field(default_factory=datetime.now)
    step_timings: Dict[str, float] = Field(default_factory=dict)
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    retry_count: int = 0
    
    def add_turn(self, turn: ConversationTurn):
        self.conversation_history.append(turn)
    
    def get_context_summary(self, last_n: int = 3) -> str:
        """Get summary of last N conversation turns for context."""
        recent_turns = self.conversation_history[-last_n:]
        return "\n".join([
            f"User: {turn.user_input}\nAgent: {turn.agent_response}"
            for turn in recent_turns
        ])
    
    def record_step_time(self, step: AgentStep, duration_ms: float):
        self.step_timings[step.value] = duration_ms
    
    @property
    def total_processing_time(self) -> float:
        return sum(self.step_timings.values())
