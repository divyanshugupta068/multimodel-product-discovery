from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database.vector_store import VectorStore
from database.models import Product as DBProduct, PriceHistory
from database.database import get_db
from models.product import Product, ProductCard, ProductFeatures, PriceInfo, ProductCategory


class ProductSearchTool:
    """
    Tool for searching products using vector similarity and filtering.
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 10
    ) -> List[ProductCard]:
        """
        Search for products matching the query.
        
        Args:
            query: Search query text
            filters: Optional filters (category, price_range, brand, etc.)
            max_results: Maximum number of results
            
        Returns:
            List of ProductCard objects with match scores
        """
        # Build vector store filter
        vector_filter = self._build_vector_filter(filters) if filters else None
        
        # Search in vector store
        vector_results = self.vector_store.search(
            query=query,
            n_results=max_results * 2,  # Get more for filtering
            filter=vector_filter
        )
        
        if not vector_results["ids"]:
            return []
        
        # Get full product details from database
        with get_db() as db:
            products = self._get_products_from_db(
                db,
                vector_results["ids"],
                filters
            )
            
            # Create ProductCard objects with match scores
            product_cards = []
            for i, product in enumerate(products):
                if i < len(vector_results["distances"]):
                    # Convert distance to similarity score (0-1)
                    distance = vector_results["distances"][i]
                    match_score = max(0, 1 - distance)
                    
                    match_reason = self._generate_match_reason(product, query)
                    
                    product_cards.append(ProductCard(
                        product=product,
                        match_score=match_score,
                        match_reason=match_reason,
                        recommended_retailer=product.best_price.retailer if product.best_price else None
                    ))
            
            # Sort by match score and limit results
            product_cards.sort(key=lambda x: x.match_score, reverse=True)
            return product_cards[:max_results]
    
    def search_by_features(
        self,
        features: Dict[str, str],
        max_results: int = 10
    ) -> List[ProductCard]:
        """
        Search products by specific features (color, brand, style, etc.).
        """
        # Build search query from features
        query_parts = []
        for key, value in features.items():
            query_parts.append(f"{key}: {value}")
        query = " ".join(query_parts)
        
        return self.search(query=query, filters=features, max_results=max_results)
    
    def search_similar(
        self,
        product_id: str,
        max_results: int = 5
    ) -> List[ProductCard]:
        """
        Find products similar to given product.
        """
        # Get product from vector store
        product_data = self.vector_store.get_product(product_id)
        if not product_data:
            return []
        
        # Use product description as query
        query = product_data.get("document", "")
        category = product_data.get("metadata", {}).get("category")
        
        filters = {"category": category} if category else None
        
        # Search for similar products
        results = self.search(query=query, filters=filters, max_results=max_results + 1)
        
        # Remove the original product from results
        return [r for r in results if r.product.id != product_id][:max_results]
    
    def _build_vector_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB filter from search filters."""
        vector_filter = {}
        
        if "category" in filters:
            vector_filter["category"] = filters["category"]
        
        if "brand" in filters:
            vector_filter["brand"] = filters["brand"]
        
        return vector_filter if vector_filter else None
    
    def _get_products_from_db(
        self,
        db: Session,
        product_ids: List[str],
        filters: Optional[Dict[str, Any]]
    ) -> List[Product]:
        """Get full product details from database."""
        query = db.query(DBProduct).filter(DBProduct.id.in_(product_ids))
        
        # Apply additional filters
        if filters:
            if "price_min" in filters or "price_max" in filters:
                # Need to join with price history
                query = query.join(PriceHistory)
                if "price_min" in filters:
                    query = query.filter(PriceHistory.amount >= filters["price_min"])
                if "price_max" in filters:
                    query = query.filter(PriceHistory.amount <= filters["price_max"])
        
        db_products = query.all()
        
        # Convert to Pydantic models
        products = []
        for db_product in db_products:
            products.append(self._db_product_to_pydantic(db_product))
        
        return products
    
    def _db_product_to_pydantic(self, db_product: DBProduct) -> Product:
        """Convert SQLAlchemy model to Pydantic model."""
        # Get latest prices
        prices = []
        for price in db_product.prices[-5:]:  # Last 5 price records
            prices.append(PriceInfo(
                amount=price.amount,
                currency=price.currency,
                retailer=price.retailer,
                availability=price.availability,
                stock_count=price.stock_count,
                last_updated=price.timestamp
            ))
        
        return Product(
            id=db_product.id,
            name=db_product.name,
            description=db_product.description,
            category=ProductCategory(db_product.category),
            features=ProductFeatures(**db_product.features),
            images=db_product.images,
            prices=prices
        )
    
    def _generate_match_reason(self, product: Product, query: str) -> str:
        """Generate explanation for why product matches query."""
        reasons = []
        
        query_lower = query.lower()
        
        # Check name match
        if any(word in product.name.lower() for word in query_lower.split()):
            reasons.append("matches product name")
        
        # Check brand match
        if product.features.brand and product.features.brand.lower() in query_lower:
            reasons.append(f"brand: {product.features.brand}")
        
        # Check color match
        if product.features.color and product.features.color.lower() in query_lower:
            reasons.append(f"color: {product.features.color}")
        
        # Check category match
        if product.category.value in query_lower:
            reasons.append(f"category: {product.category.value}")
        
        if not reasons:
            return "Similar to your search based on product features"
        
        return "Matches " + ", ".join(reasons)
