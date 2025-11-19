from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from collections import defaultdict
import numpy as np

from database.database import get_db
from database.models import Product as DBProduct, SearchHistory, Review
from database.vector_store import VectorStore
from models.product import ProductCard
from .product_search import ProductSearchTool


class RecommendationTool:
    """
    Tool for generating product recommendations using collaborative filtering
    and content-based approaches.
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.search_tool = ProductSearchTool()
    
    def get_recommendations(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None,
        max_results: int = 10
    ) -> List[ProductCard]:
        """
        Get personalized product recommendations.
        
        Args:
            user_id: User ID for personalization
            session_id: Session ID for anonymous users
            context: Additional context (browsing history, cart items, etc.)
            max_results: Maximum number of recommendations
            
        Returns:
            List of recommended products
        """
        recommendations = []
        
        # Strategy 1: Collaborative filtering based on user history
        if user_id:
            collab_recs = self._collaborative_filtering(user_id, max_results // 2)
            recommendations.extend(collab_recs)
        
        # Strategy 2: Content-based on recent browsing
        if session_id or (context and context.get("browsing_history")):
            content_recs = self._content_based_recommendations(
                user_id, session_id, context, max_results // 2
            )
            recommendations.extend(content_recs)
        
        # Strategy 3: Trending products as fallback
        if len(recommendations) < max_results:
            trending = self._get_trending_products(max_results - len(recommendations))
            recommendations.extend(trending)
        
        # Deduplicate and rank
        seen_ids = set()
        unique_recs = []
        for rec in recommendations:
            if rec.product.id not in seen_ids:
                unique_recs.append(rec)
                seen_ids.add(rec.product.id)
        
        return unique_recs[:max_results]
    
    def get_similar_products(
        self,
        product_id: str,
        max_results: int = 5
    ) -> List[ProductCard]:
        """
        Get products similar to a given product (content-based).
        """
        return self.search_tool.search_similar(product_id, max_results)
    
    def get_frequently_bought_together(
        self,
        product_id: str,
        max_results: int = 5
    ) -> List[ProductCard]:
        """
        Find products frequently bought together (association rules).
        """
        with get_db() as db:
            # Get search sessions that included this product
            sessions_with_product = db.query(SearchHistory.session_id).filter(
                SearchHistory.clicked_products.contains([product_id])
            ).distinct().all()
            
            session_ids = [s[0] for s in sessions_with_product]
            
            if not session_ids:
                # Fallback to similar products
                return self.get_similar_products(product_id, max_results)
            
            # Get other products from those sessions
            other_products = db.query(SearchHistory).filter(
                SearchHistory.session_id.in_(session_ids)
            ).all()
            
            # Count co-occurrences
            product_counts = defaultdict(int)
            for history in other_products:
                for pid in history.clicked_products:
                    if pid != product_id:
                        product_counts[pid] += 1
                for pid in history.added_to_cart:
                    if pid != product_id:
                        product_counts[pid] += 2  # Weight cart adds more
            
            # Get top co-occurring products
            top_products = sorted(
                product_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max_results]
            
            # Convert to ProductCard
            product_cards = []
            for pid, count in top_products:
                product = db.query(DBProduct).filter(DBProduct.id == pid).first()
                if product:
                    product_pydantic = self.search_tool._db_product_to_pydantic(product)
                    support = count / len(session_ids)
                    product_cards.append(ProductCard(
                        product=product_pydantic,
                        match_score=min(support, 1.0),
                        match_reason=f"Frequently bought together ({int(support * 100)}% of customers)"
                    ))
            
            return product_cards
    
    def _collaborative_filtering(
        self,
        user_id: str,
        max_results: int
    ) -> List[ProductCard]:
        """
        Collaborative filtering: recommend based on similar users.
        """
        with get_db() as db:
            # Get user's interaction history
            user_history = db.query(SearchHistory).filter(
                SearchHistory.user_id == user_id
            ).all()
            
            if not user_history:
                return []
            
            # Get products user has interacted with
            user_products = set()
            for history in user_history:
                user_products.update(history.clicked_products)
                user_products.update(history.added_to_cart)
            
            if not user_products:
                return []
            
            # Find users with similar taste (simplified - would use proper similarity metrics)
            similar_users_history = db.query(SearchHistory).filter(
                SearchHistory.user_id != user_id
            ).all()
            
            # Find products that similar users liked
            similar_user_products = defaultdict(int)
            for history in similar_users_history:
                overlap = len(set(history.clicked_products) & user_products)
                if overlap > 0:
                    # Weight by overlap
                    for pid in history.clicked_products:
                        if pid not in user_products:
                            similar_user_products[pid] += overlap
                    for pid in history.added_to_cart:
                        if pid not in user_products:
                            similar_user_products[pid] += overlap * 2
            
            # Get top recommendations
            top_recs = sorted(
                similar_user_products.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max_results]
            
            # Convert to ProductCard
            product_cards = []
            for pid, score in top_recs:
                product = db.query(DBProduct).filter(DBProduct.id == pid).first()
                if product:
                    product_pydantic = self.search_tool._db_product_to_pydantic(product)
                    product_cards.append(ProductCard(
                        product=product_pydantic,
                        match_score=min(score / 10.0, 1.0),  # Normalize score
                        match_reason="Based on users with similar taste"
                    ))
            
            return product_cards
    
    def _content_based_recommendations(
        self,
        user_id: Optional[str],
        session_id: Optional[str],
        context: Optional[Dict],
        max_results: int
    ) -> List[ProductCard]:
        """
        Content-based: recommend based on browsing history and context.
        """
        browsing_history = []
        
        # Get browsing history from context or database
        if context and context.get("browsing_history"):
            browsing_history = context["browsing_history"]
        elif session_id:
            with get_db() as db:
                history = db.query(SearchHistory).filter(
                    SearchHistory.session_id == session_id
                ).order_by(SearchHistory.timestamp.desc()).limit(5).all()
                for h in history:
                    browsing_history.extend(h.clicked_products)
        
        if not browsing_history:
            return []
        
        # Get similar products to recently browsed items
        all_recommendations = []
        for product_id in browsing_history[-3:]:  # Last 3 products
            similar = self.search_tool.search_similar(product_id, max_results=3)
            all_recommendations.extend(similar)
        
        # Deduplicate
        seen_ids = set()
        unique_recs = []
        for rec in all_recommendations:
            if rec.product.id not in seen_ids and rec.product.id not in browsing_history:
                unique_recs.append(rec)
                seen_ids.add(rec.product.id)
        
        return unique_recs[:max_results]
    
    def _get_trending_products(self, max_results: int) -> List[ProductCard]:
        """
        Get trending products based on recent activity.
        """
        with get_db() as db:
            # Get products with most recent interactions
            from datetime import datetime, timedelta
            recent_date = datetime.now() - timedelta(days=7)
            
            recent_history = db.query(SearchHistory).filter(
                SearchHistory.timestamp >= recent_date
            ).all()
            
            product_scores = defaultdict(int)
            for history in recent_history:
                for pid in history.clicked_products:
                    product_scores[pid] += 1
                for pid in history.added_to_cart:
                    product_scores[pid] += 3
            
            # Get top trending
            trending = sorted(
                product_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max_results]
            
            # Convert to ProductCard
            product_cards = []
            for pid, score in trending:
                product = db.query(DBProduct).filter(DBProduct.id == pid).first()
                if product:
                    product_pydantic = self.search_tool._db_product_to_pydantic(product)
                    product_cards.append(ProductCard(
                        product=product_pydantic,
                        match_score=0.8,
                        match_reason="Trending now"
                    ))
            
            return product_cards
