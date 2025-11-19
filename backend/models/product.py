from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class ProductCategory(str, Enum):
    CLOTHING = "clothing"
    ELECTRONICS = "electronics"
    HOME = "home"
    SPORTS = "sports"
    BEAUTY = "beauty"
    BOOKS = "books"
    OTHER = "other"


class PriceInfo(BaseModel):
    amount: float = Field(..., description="Price amount")
    currency: str = Field(default="USD", description="Currency code")
    retailer: str = Field(..., description="Retailer name")
    availability: bool = Field(default=True, description="Product availability")
    stock_count: Optional[int] = Field(None, description="Stock count if available")
    last_updated: datetime = Field(default_factory=datetime.now)


class ProductFeatures(BaseModel):
    color: Optional[str] = None
    size: Optional[str] = None
    brand: Optional[str] = None
    material: Optional[str] = None
    style: Optional[str] = None
    additional_features: Dict[str, str] = Field(default_factory=dict)


class ReviewSummary(BaseModel):
    average_rating: float = Field(..., ge=0, le=5)
    total_reviews: int = Field(..., ge=0)
    sentiment_score: float = Field(..., ge=-1, le=1)
    key_positive_points: List[str] = Field(default_factory=list)
    key_negative_points: List[str] = Field(default_factory=list)
    top_keywords: List[str] = Field(default_factory=list)


class Product(BaseModel):
    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    category: ProductCategory
    features: ProductFeatures
    images: List[HttpUrl] = Field(default_factory=list)
    prices: List[PriceInfo] = Field(default_factory=list)
    reviews: Optional[ReviewSummary] = None
    embedding: Optional[List[float]] = Field(None, exclude=True)
    
    @property
    def best_price(self) -> Optional[PriceInfo]:
        if not self.prices:
            return None
        return min(self.prices, key=lambda p: p.amount)
    
    @property
    def price_range(self) -> Optional[tuple[float, float]]:
        if not self.prices:
            return None
        amounts = [p.amount for p in self.prices]
        return (min(amounts), max(amounts))


class ProductCard(BaseModel):
    product: Product
    match_score: float = Field(..., ge=0, le=1, description="Relevance score")
    match_reason: str = Field(..., description="Why this product matches the query")
    recommended_retailer: Optional[str] = None
    quick_actions: List[str] = Field(
        default_factory=lambda: ["view_details", "compare", "add_to_cart"]
    )


class ProductComparison(BaseModel):
    products: List[Product] = Field(..., min_length=2, max_length=5)
    comparison_table: Dict[str, List[str]] = Field(
        ..., description="Feature comparison matrix"
    )
    winner: Optional[str] = Field(
        None, description="Product ID of recommended product"
    )
    winner_reason: Optional[str] = Field(
        None, description="Explanation of why this product is recommended"
    )
    key_differences: List[str] = Field(default_factory=list)


class PurchaseAction(BaseModel):
    action_type: str = Field(..., description="add_to_cart, checkout, save_for_later")
    product_id: str
    retailer: str
    quantity: int = Field(default=1, ge=1)
    selected_features: Optional[Dict[str, str]] = None
    estimated_total: Optional[float] = None
