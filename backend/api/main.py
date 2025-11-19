from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import base64
from typing import Optional
import uvicorn

from models.query import QueryRequest, QueryResponse, QueryType
from agents.product_discovery_agent import ProductDiscoveryAgent
from config import get_settings
from database.database import init_db

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Multimodal Product Discovery API",
    description="AI-powered product discovery with vision, voice, and text",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = ProductDiscoveryAgent()


@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources on startup."""
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Multimodal Product Discovery API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "text_query": "/api/query/text",
            "image_query": "/api/query/image",
            "voice_query": "/api/query/voice",
            "multimodal_query": "/api/query/multimodal",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vision_enabled": settings.enable_vision_processing,
        "speech_enabled": settings.enable_speech_processing
    }


@app.post("/api/query/text", response_model=QueryResponse)
async def query_text(request: QueryRequest):
    """
    Process text-based product query.
    
    Example:
    ```json
    {
        "query_text": "Find me a red leather jacket under $200",
        "query_type": "text",
        "max_results": 10
    }
    ```
    """
    try:
        if request.query_type != QueryType.TEXT:
            request.query_type = QueryType.TEXT
        
        response = await agent.process_query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/image", response_model=QueryResponse)
async def query_image(
    image: UploadFile = File(...),
    query_text: Optional[str] = Form(None),
    max_results: int = Form(10),
    session_id: Optional[str] = Form(None)
):
    """
    Process image-based product query.
    Upload an image to find similar products.
    """
    try:
        # Read and encode image
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create request
        request = QueryRequest(
            query_text=query_text,
            image_data=image_base64,
            query_type=QueryType.IMAGE,
            max_results=max_results,
            session_id=session_id
        )
        
        response = await agent.process_query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/voice", response_model=QueryResponse)
async def query_voice(
    audio: UploadFile = File(...),
    max_results: int = Form(10),
    session_id: Optional[str] = Form(None)
):
    """
    Process voice-based product query.
    Upload audio file (WAV, MP3, etc.) with voice command.
    """
    try:
        # Read and encode audio
        audio_bytes = await audio.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Create request
        request = QueryRequest(
            audio_data=audio_base64,
            query_type=QueryType.VOICE,
            max_results=max_results,
            session_id=session_id
        )
        
        response = await agent.process_query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/multimodal", response_model=QueryResponse)
async def query_multimodal(
    query_text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    max_results: int = Form(10),
    session_id: Optional[str] = Form(None)
):
    """
    Process multimodal query combining text, image, and/or voice.
    """
    try:
        image_base64 = None
        audio_base64 = None
        
        if image:
            image_bytes = await image.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        if audio:
            audio_bytes = await audio.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Create request
        request = QueryRequest(
            query_text=query_text,
            image_data=image_base64,
            audio_data=audio_base64,
            query_type=QueryType.MULTIMODAL,
            max_results=max_results,
            session_id=session_id
        )
        
        response = await agent.process_query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Get product details by ID."""
    from database.database import get_db
    from database.models import Product
    
    try:
        with get_db() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            return {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "category": product.category,
                "features": product.features,
                "images": product.images
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}/reviews")
async def get_product_reviews(product_id: str, limit: int = 10):
    """Get reviews for a specific product."""
    from tools.review_analysis import ReviewAnalysisTool
    
    try:
        review_tool = ReviewAnalysisTool()
        reviews = review_tool.get_most_helpful_reviews(product_id, limit)
        return {"product_id": product_id, "reviews": reviews}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}/prices")
async def get_product_prices(product_id: str):
    """Get price comparison for a product."""
    from tools.price_comparison import PriceComparisonTool
    
    try:
        price_tool = PriceComparisonTool()
        comparison = price_tool.compare_prices(product_id)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations")
async def get_recommendations(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 10
):
    """Get personalized product recommendations."""
    from tools.recommendation import RecommendationTool
    
    try:
        rec_tool = RecommendationTool()
        recommendations = rec_tool.get_recommendations(
            user_id=user_id,
            session_id=session_id,
            max_results=limit
        )
        return {"recommendations": [r.dict() for r in recommendations]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        workers=1  # Use 1 for development
    )
