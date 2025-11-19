from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)
    brand = Column(String, index=True)
    
    # Features stored as JSON
    features = Column(JSON, default={})
    
    # Images stored as JSON array of URLs
    images = Column(JSON, default=[])
    
    # Vector embedding (stored separately in vector DB)
    embedding_id = Column(String, index=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    prices = relationship("PriceHistory", back_populates="product")
    reviews = relationship("Review", back_populates="product")


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    retailer = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    availability = Column(Boolean, default=True)
    stock_count = Column(Integer)
    url = Column(String)
    
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    # Relationship
    product = relationship("Product", back_populates="prices")


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"))
    
    rating = Column(Float, nullable=False)
    title = Column(String)
    content = Column(Text)
    sentiment_score = Column(Float)  # -1 to 1
    
    helpful_count = Column(Integer, default=0)
    verified_purchase = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationship
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    
    # Preferences stored as JSON
    preferences = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)
    
    # Relationships
    reviews = relationship("Review", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user")


class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, index=True)
    
    query_text = Column(Text)
    query_type = Column(String)  # text, image, voice, multimodal
    intent = Column(String)
    
    # Results stored as JSON array of product IDs
    results = Column(JSON, default=[])
    
    # User interaction
    clicked_products = Column(JSON, default=[])
    added_to_cart = Column(JSON, default=[])
    
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    # Relationship
    user = relationship("User", back_populates="search_history")
