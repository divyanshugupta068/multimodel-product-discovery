import asyncio
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

from models.vision import VisionAnalysis, VisionComparisonResult, VisualFeatures
from .gpt4v_processor import GPT4VisionProcessor
from .claude_processor import ClaudeVisionProcessor
from config import get_settings


class VisionOrchestrator:
    """
    Orchestrates vision processing across multiple models (GPT-4V and Claude 3.5).
    Supports parallel execution and result comparison.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.gpt4v = GPT4VisionProcessor()
        self.claude = ClaudeVisionProcessor()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def analyze_with_best_model(self, image_data: str) -> VisionAnalysis:
        """
        Analyze image with the default model, fallback to alternative if needed.
        """
        try:
            # Try GPT-4V first (default)
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.gpt4v.analyze_image,
                image_data
            )
            return result
        except Exception as e:
            print(f"GPT-4V failed: {e}. Falling back to Claude...")
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.claude.analyze_image,
                    image_data
                )
                return result
            except Exception as e2:
                raise Exception(f"All vision models failed. GPT-4V: {e}, Claude: {e2}")
    
    async def analyze_with_both_models(self, image_data: str) -> VisionComparisonResult:
        """
        Analyze image with both GPT-4V and Claude 3.5 in parallel for comparison.
        """
        # Run both models in parallel
        gpt4v_task = asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.gpt4v.analyze_image,
            image_data
        )
        claude_task = asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.claude.analyze_image,
            image_data
        )
        
        try:
            results = await asyncio.gather(gpt4v_task, claude_task, return_exceptions=True)
            
            gpt4v_result = results[0] if not isinstance(results[0], Exception) else None
            claude_result = results[1] if not isinstance(results[1], Exception) else None
            
            if gpt4v_result is None and claude_result is None:
                raise Exception("Both vision models failed")
            
            # Compare and combine results
            comparison = self._compare_results(gpt4v_result, claude_result)
            
            return comparison
            
        except Exception as e:
            raise Exception(f"Vision comparison failed: {str(e)}")
    
    def _compare_results(
        self,
        gpt4v_result: Optional[VisionAnalysis],
        claude_result: Optional[VisionAnalysis]
    ) -> VisionComparisonResult:
        """
        Compare results from both models and generate combined analysis.
        """
        if gpt4v_result is None and claude_result is None:
            raise ValueError("At least one result must be available")
        
        # If only one result available, use it
        if gpt4v_result is None:
            return VisionComparisonResult(
                claude_analysis=claude_result,
                agreement_score=1.0,
                combined_features=claude_result.visual_features,
                recommended_queries=claude_result.search_queries
            )
        
        if claude_result is None:
            return VisionComparisonResult(
                gpt4v_analysis=gpt4v_result,
                agreement_score=1.0,
                combined_features=gpt4v_result.visual_features,
                recommended_queries=gpt4v_result.search_queries
            )
        
        # Calculate agreement score
        agreement_score = self._calculate_agreement(gpt4v_result, claude_result)
        
        # Combine features from both models
        combined_features = self._combine_features(
            gpt4v_result.visual_features,
            claude_result.visual_features
        )
        
        # Merge and deduplicate search queries
        all_queries = list(set(
            gpt4v_result.search_queries + claude_result.search_queries
        ))
        
        return VisionComparisonResult(
            gpt4v_analysis=gpt4v_result,
            claude_analysis=claude_result,
            agreement_score=agreement_score,
            combined_features=combined_features,
            recommended_queries=all_queries[:5]
        )
    
    def _calculate_agreement(
        self,
        result1: VisionAnalysis,
        result2: VisionAnalysis
    ) -> float:
        """
        Calculate agreement score between two vision analyses.
        """
        scores = []
        
        # Compare product types
        if result1.product_identification.product_type == result2.product_identification.product_type:
            scores.append(1.0)
        else:
            scores.append(0.0)
        
        # Compare brands
        brand1 = result1.product_identification.brand
        brand2 = result2.product_identification.brand
        if brand1 and brand2:
            scores.append(1.0 if brand1.lower() == brand2.lower() else 0.0)
        
        # Compare categories
        if result1.visual_features.category == result2.visual_features.category:
            scores.append(1.0)
        else:
            scores.append(0.5)
        
        # Compare colors
        colors1 = set(c.lower() for c in result1.visual_features.colors)
        colors2 = set(c.lower() for c in result2.visual_features.colors)
        if colors1 and colors2:
            color_overlap = len(colors1 & colors2) / max(len(colors1), len(colors2))
            scores.append(color_overlap)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _combine_features(
        self,
        features1: VisualFeatures,
        features2: VisualFeatures
    ) -> VisualFeatures:
        """
        Combine visual features from both models, preferring higher confidence.
        """
        # Merge colors and deduplicate
        combined_colors = list(set(
            [c.lower() for c in features1.colors] +
            [c.lower() for c in features2.colors]
        ))[:3]
        
        # Use higher confidence style
        style = features1.style if features1.confidence_score >= features2.confidence_score else features2.style
        
        # Use higher confidence category
        category = features1.category if features1.confidence_score >= features2.confidence_score else features2.category
        
        # Merge brands
        brand = features1.brand or features2.brand
        
        # Merge key features
        combined_features = list(set(features1.key_features + features2.key_features))
        
        # Average confidence scores
        avg_confidence = (features1.confidence_score + features2.confidence_score) / 2
        
        return VisualFeatures(
            colors=combined_colors,
            style=style,
            category=category,
            brand=brand,
            text_on_image=list(set(features1.text_on_image + features2.text_on_image)),
            key_features=combined_features,
            confidence_score=avg_confidence
        )
