from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter
import re

from database.database import get_db
from database.models import Product as DBProduct, Review
from models.product import ReviewSummary


class ReviewAnalysisTool:
    """
    Tool for analyzing product reviews and extracting insights.
    """
    
    def analyze_reviews(self, product_id: str) -> ReviewSummary:
        """
        Analyze all reviews for a product and generate summary.
        
        Args:
            product_id: Product ID to analyze
            
        Returns:
            ReviewSummary with aggregated insights
        """
        with get_db() as db:
            reviews = db.query(Review).filter(Review.product_id == product_id).all()
            
            if not reviews:
                return ReviewSummary(
                    average_rating=0.0,
                    total_reviews=0,
                    sentiment_score=0.0,
                    key_positive_points=[],
                    key_negative_points=[],
                    top_keywords=[]
                )
            
            # Calculate statistics
            ratings = [r.rating for r in reviews]
            sentiments = [r.sentiment_score for r in reviews if r.sentiment_score is not None]
            
            average_rating = sum(ratings) / len(ratings)
            average_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            # Extract key points
            positive_reviews = [r for r in reviews if r.rating >= 4]
            negative_reviews = [r for r in reviews if r.rating <= 2]
            
            positive_points = self._extract_key_points(
                [r.content for r in positive_reviews if r.content],
                max_points=5
            )
            negative_points = self._extract_key_points(
                [r.content for r in negative_reviews if r.content],
                max_points=5
            )
            
            # Extract keywords
            all_content = [r.content for r in reviews if r.content]
            keywords = self._extract_keywords(all_content, max_keywords=10)
            
            return ReviewSummary(
                average_rating=round(average_rating, 2),
                total_reviews=len(reviews),
                sentiment_score=round(average_sentiment, 2),
                key_positive_points=positive_points,
                key_negative_points=negative_points,
                top_keywords=keywords
            )
    
    def get_reviews_by_rating(
        self,
        product_id: str,
        min_rating: float = 0,
        max_rating: float = 5,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get reviews filtered by rating range.
        """
        with get_db() as db:
            reviews = db.query(Review).filter(
                and_(
                    Review.product_id == product_id,
                    Review.rating >= min_rating,
                    Review.rating <= max_rating
                )
            ).order_by(Review.helpful_count.desc()).limit(limit).all()
            
            return [
                {
                    "rating": r.rating,
                    "title": r.title,
                    "content": r.content,
                    "sentiment_score": r.sentiment_score,
                    "helpful_count": r.helpful_count,
                    "verified_purchase": r.verified_purchase,
                    "created_at": r.created_at
                }
                for r in reviews
            ]
    
    def get_most_helpful_reviews(
        self,
        product_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get most helpful reviews for a product.
        """
        return self.get_reviews_by_rating(product_id, 0, 5, limit)
    
    def compare_reviews(
        self,
        product_ids: List[str]
    ) -> Dict[str, ReviewSummary]:
        """
        Compare review summaries across multiple products.
        """
        comparisons = {}
        for product_id in product_ids:
            comparisons[product_id] = self.analyze_reviews(product_id)
        return comparisons
    
    def get_rating_distribution(
        self,
        product_id: str
    ) -> Dict[int, int]:
        """
        Get distribution of ratings (1-5 stars).
        """
        with get_db() as db:
            ratings = db.query(Review.rating).filter(
                Review.product_id == product_id
            ).all()
            
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for rating, in ratings:
                star = int(round(rating))
                if 1 <= star <= 5:
                    distribution[star] += 1
            
            return distribution
    
    def _extract_key_points(
        self,
        review_texts: List[str],
        max_points: int = 5
    ) -> List[str]:
        """
        Extract key points from review texts.
        This is a simplified version - production would use NLP models.
        """
        if not review_texts:
            return []
        
        # Simple sentence extraction based on frequency
        all_sentences = []
        for text in review_texts:
            sentences = text.split('.')
            all_sentences.extend([s.strip() for s in sentences if len(s.strip()) > 20])
        
        # Count sentence occurrences (similar sentences)
        sentence_counts = Counter(all_sentences)
        
        # Get most common
        common_sentences = [s for s, count in sentence_counts.most_common(max_points)]
        
        return common_sentences[:max_points]
    
    def _extract_keywords(
        self,
        review_texts: List[str],
        max_keywords: int = 10
    ) -> List[str]:
        """
        Extract keywords from review texts.
        Simplified version - production would use TF-IDF or keyword extraction models.
        """
        if not review_texts:
            return []
        
        # Combine all text
        all_text = " ".join(review_texts).lower()
        
        # Remove common words
        stop_words = set([
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "up", "about", "into", "through", "during",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "may", "might",
            "this", "that", "these", "those", "it", "its", "i", "you", "he", "she",
            "we", "they", "them", "their", "what", "which", "who", "when", "where",
            "why", "how", "not", "very", "really", "just", "quite"
        ])
        
        # Extract words
        words = re.findall(r'\b\w+\b', all_text)
        words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Count frequencies
        word_counts = Counter(words)
        
        # Get most common
        keywords = [word for word, count in word_counts.most_common(max_keywords)]
        
        return keywords
    
    def sentiment_analysis(self, text: str) -> float:
        """
        Perform sentiment analysis on text.
        Returns score between -1 (negative) and 1 (positive).
        
        This is a simplified version - production would use proper sentiment models.
        """
        positive_words = set([
            "good", "great", "excellent", "amazing", "wonderful", "fantastic",
            "perfect", "love", "best", "awesome", "nice", "beautiful", "quality",
            "recommend", "happy", "satisfied", "pleased", "impressive"
        ])
        
        negative_words = set([
            "bad", "poor", "terrible", "horrible", "awful", "worst", "hate",
            "disappointing", "disappointed", "waste", "broken", "defective",
            "cheap", "useless", "garbage", "unhappy", "dissatisfied"
        ])
        
        words = re.findall(r'\b\w+\b', text.lower())
        
        positive_count = sum(1 for w in words if w in positive_words)
        negative_count = sum(1 for w in words if w in negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, sentiment))
