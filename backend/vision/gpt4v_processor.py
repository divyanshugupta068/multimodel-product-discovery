import base64
import time
from typing import Optional
from openai import OpenAI
from PIL import Image
import io

from models.vision import VisionAnalysis, VisualFeatures, ProductIdentification, VisionModel
from config import get_settings


class GPT4VisionProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.default_vision_model
    
    def analyze_image(self, image_data: str) -> VisionAnalysis:
        """
        Analyze product image using GPT-4 Vision.
        
        Args:
            image_data: Base64 encoded image string
            
        Returns:
            VisionAnalysis with extracted features and product identification
        """
        start_time = time.time()
        
        try:
            # Prepare the vision prompt
            prompt = self._create_vision_prompt()
            
            # Call GPT-4V API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            # Parse response
            content = response.choices[0].message.content
            analysis = self._parse_vision_response(content)
            
            processing_time = (time.time() - start_time) * 1000
            
            return VisionAnalysis(
                model_used=VisionModel.GPT4V,
                visual_features=analysis["visual_features"],
                product_identification=analysis["product_identification"],
                search_queries=analysis["search_queries"],
                processing_time_ms=processing_time,
                raw_response=content
            )
            
        except Exception as e:
            raise Exception(f"GPT-4V processing failed: {str(e)}")
    
    def _create_vision_prompt(self) -> str:
        return """Analyze this product image and provide detailed information in the following structure:

1. VISUAL FEATURES:
   - Dominant colors (list up to 3)
   - Style description (modern, vintage, casual, formal, etc.)
   - Product category (clothing, electronics, home, sports, beauty, books, other)
   - Brand (if visible)
   - Any text visible on the product
   - Key visual features (texture, pattern, shape, etc.)
   - Confidence score (0-1)

2. PRODUCT IDENTIFICATION:
   - Product name (if identifiable)
   - Product type (specific category like "leather jacket", "smartphone", etc.)
   - Brand (if identifiable)
   - Model (if identifiable)
   - Confidence score (0-1)

3. SEARCH QUERIES:
   Generate 3-5 search queries that would help find this product or similar products online.

Format your response as JSON with the following structure:
{
  "visual_features": {
    "colors": ["color1", "color2"],
    "style": "style description",
    "category": "category",
    "brand": "brand or null",
    "text_on_image": ["text1", "text2"],
    "key_features": ["feature1", "feature2"],
    "confidence_score": 0.0-1.0
  },
  "product_identification": {
    "product_name": "name or null",
    "product_type": "type",
    "brand": "brand or null",
    "model": "model or null",
    "confidence": 0.0-1.0
  },
  "search_queries": ["query1", "query2", "query3"]
}"""
    
    def _parse_vision_response(self, response: str) -> dict:
        """Parse GPT-4V response into structured format."""
        import json
        
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            # Validate and create Pydantic models
            visual_features = VisualFeatures(**data["visual_features"])
            product_identification = ProductIdentification(**data["product_identification"])
            search_queries = data["search_queries"]
            
            return {
                "visual_features": visual_features,
                "product_identification": product_identification,
                "search_queries": search_queries
            }
            
        except Exception as e:
            # Fallback parsing if JSON extraction fails
            return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> dict:
        """Fallback parser for non-JSON responses."""
        return {
            "visual_features": VisualFeatures(
                colors=["unknown"],
                style="unknown",
                category="other",
                key_features=["Could not parse detailed features"],
                confidence_score=0.5
            ),
            "product_identification": ProductIdentification(
                product_type="unknown",
                confidence=0.5
            ),
            "search_queries": ["product in image"]
        }
    
    def validate_image(self, image_data: str) -> bool:
        """Validate image data before processing."""
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check image size (max 5MB)
            if len(image_bytes) > 5 * 1024 * 1024:
                raise ValueError("Image size exceeds 5MB limit")
            
            # Check image dimensions
            if image.width < 50 or image.height < 50:
                raise ValueError("Image too small (minimum 50x50 pixels)")
            
            return True
            
        except Exception as e:
            raise ValueError(f"Invalid image data: {str(e)}")
