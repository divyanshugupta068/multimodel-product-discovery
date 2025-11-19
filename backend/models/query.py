from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

from .product import ProductCard, ProductComparison, PurchaseAction


class Intent(str, Enum):
    SEARCH = "search"
    COMPARE = "compare"
    PURCHASE = "purchase"
    QUESTION = "question"
    RECOMMENDATION = "recommendation"
    PRICE_CHECK = "price_check"
    AVAILABILITY_CHECK = "availability_check"
    REVIEW_ANALYSIS = "review_analysis"


class QueryType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    MULTIMODAL = "multimodal"


class QueryFilters(BaseModel):
    categories: Optional[List[str]] = None
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    brands: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    in_stock_only: bool = True
    retailers: Optional[List[str]] = None


class QueryRequest(BaseModel):
    query_text: Optional[str] = None
    image_data: Optional[str] = Field(None, description="Base64 encoded image")
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio")
    query_type: QueryType
    filters: Optional[QueryFilters] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_results: int = Field(default=10, ge=1, le=50)


class QueryResponse(BaseModel):
    query_id: str = Field(..., description="Unique query identifier")
    intent: Intent
    intent_confidence: float = Field(..., ge=0, le=1)
    
    # Response content
    message: str = Field(..., description="Natural language response")
    products: List[ProductCard] = Field(default_factory=list)
    comparison: Optional[ProductComparison] = None
    purchase_action: Optional[PurchaseAction] = None
    
    # Metadata
    processing_time_ms: float
    models_used: Dict[str, str] = Field(default_factory=dict)
    tool_calls: List[str] = Field(default_factory=list)
    
    # Follow-up suggestions
    suggested_questions: List[str] = Field(default_factory=list)
    suggested_refinements: List[str] = Field(default_factory=list)
    
    # Performance metrics
    latency_breakdown: Dict[str, float] = Field(default_factory=dict)
    cost_estimate: Optional[float] = None
    
    timestamp: datetime = Field(default_factory=datetime.now)


class QueryError(BaseModel):
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
