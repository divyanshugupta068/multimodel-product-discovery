from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class LatencyMetrics(BaseModel):
    """Latency measurements for different components."""
    vision_processing_ms: Optional[float] = None
    speech_processing_ms: Optional[float] = None
    intent_classification_ms: Optional[float] = None
    tool_execution_ms: Optional[float] = None
    response_generation_ms: Optional[float] = None
    total_latency_ms: float
    
    @property
    def meets_target(self) -> bool:
        """Check if latency meets < 4000ms target."""
        return self.total_latency_ms < 4000


class AccuracyMetrics(BaseModel):
    """Accuracy measurements for model outputs."""
    product_identification_precision: Optional[float] = Field(None, ge=0, le=1)
    product_identification_recall: Optional[float] = Field(None, ge=0, le=1)
    product_identification_f1: Optional[float] = Field(None, ge=0, le=1)
    intent_classification_accuracy: Optional[float] = Field(None, ge=0, le=1)
    recommendation_relevance: Optional[float] = Field(None, ge=0, le=1)
    hallucination_rate: Optional[float] = Field(None, ge=0, le=1)
    
    @property
    def meets_target(self) -> bool:
        """Check if precision meets > 85% target."""
        if self.product_identification_precision:
            return self.product_identification_precision > 0.85
        return False


class CostMetrics(BaseModel):
    """Cost tracking for API calls."""
    openai_cost: float = 0.0
    anthropic_cost: float = 0.0
    deepgram_cost: float = 0.0
    total_cost: float = 0.0
    cost_per_query: float = 0.0
    
    @property
    def meets_target(self) -> bool:
        """Check if cost meets < $0.10 per query target."""
        return self.cost_per_query < 0.10


class ModelComparisonMetrics(BaseModel):
    """Comparison metrics between GPT-4V and Claude 3.5."""
    gpt4v_accuracy: Optional[float] = None
    claude_accuracy: Optional[float] = None
    gpt4v_latency_ms: Optional[float] = None
    claude_latency_ms: Optional[float] = None
    gpt4v_cost: Optional[float] = None
    claude_cost: Optional[float] = None
    agreement_rate: Optional[float] = Field(None, ge=0, le=1)


class EvaluationMetrics(BaseModel):
    """Complete evaluation metrics for a test run."""
    test_id: str
    test_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Component metrics
    latency: LatencyMetrics
    accuracy: AccuracyMetrics
    cost: CostMetrics
    model_comparison: Optional[ModelComparisonMetrics] = None
    
    # Summary
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    
    # Additional metadata
    model_versions: Dict[str, str] = Field(default_factory=dict)
    test_config: Dict[str, any] = Field(default_factory=dict)
    
    @property
    def overall_pass(self) -> bool:
        """Check if all targets are met."""
        return (
            self.latency.meets_target and
            self.accuracy.meets_target and
            self.cost.meets_target
        )


class TestCase(BaseModel):
    """Individual test case definition."""
    test_id: str
    name: str
    query_type: str  # text, image, voice, multimodal
    input_data: Dict[str, any]
    expected_output: Dict[str, any]
    expected_intent: Optional[str] = None
    expected_products: Optional[List[str]] = None  # Product IDs or names
    min_accuracy: float = 0.85
    max_latency_ms: float = 4000
