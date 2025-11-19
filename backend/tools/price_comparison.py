from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database.database import get_db
from database.models import Product as DBProduct, PriceHistory
from models.product import Product, PriceInfo


class PriceComparisonTool:
    """
    Tool for comparing prices across multiple retailers.
    """
    
    def compare_prices(self, product_id: str) -> Dict[str, any]:
        """
        Get price comparison across all retailers for a product.
        
        Args:
            product_id: Product ID to compare
            
        Returns:
            Dictionary with price comparison data
        """
        with get_db() as db:
            # Get product
            product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Get latest prices from each retailer
            latest_prices = db.query(
                PriceHistory.retailer,
                func.max(PriceHistory.timestamp).label("latest_time")
            ).filter(
                PriceHistory.product_id == product_id
            ).group_by(
                PriceHistory.retailer
            ).subquery()
            
            prices_query = db.query(PriceHistory).join(
                latest_prices,
                and_(
                    PriceHistory.retailer == latest_prices.c.retailer,
                    PriceHistory.timestamp == latest_prices.c.latest_time
                )
            ).filter(PriceHistory.product_id == product_id)
            
            prices = prices_query.all()
            
            if not prices:
                return {
                    "product_id": product_id,
                    "product_name": product.name,
                    "prices": [],
                    "best_price": None,
                    "price_range": None,
                    "average_price": None
                }
            
            # Convert to PriceInfo objects
            price_infos = [
                PriceInfo(
                    amount=p.amount,
                    currency=p.currency,
                    retailer=p.retailer,
                    availability=p.availability,
                    stock_count=p.stock_count,
                    last_updated=p.timestamp
                )
                for p in prices
            ]
            
            # Calculate statistics
            available_prices = [p.amount for p in price_infos if p.availability]
            
            if available_prices:
                best_price = min(price_infos, key=lambda x: x.amount if x.availability else float('inf'))
                price_range = (min(available_prices), max(available_prices))
                average_price = sum(available_prices) / len(available_prices)
            else:
                best_price = None
                price_range = None
                average_price = None
            
            return {
                "product_id": product_id,
                "product_name": product.name,
                "prices": price_infos,
                "best_price": best_price,
                "price_range": price_range,
                "average_price": average_price,
                "savings": price_range[1] - price_range[0] if price_range else 0
            }
    
    def compare_multiple_products(
        self,
        product_ids: List[str]
    ) -> List[Dict[str, any]]:
        """
        Compare prices for multiple products.
        """
        return [self.compare_prices(pid) for pid in product_ids]
    
    def get_price_history(
        self,
        product_id: str,
        days: int = 30,
        retailer: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Get price history for a product.
        
        Args:
            product_id: Product ID
            days: Number of days to look back
            retailer: Optional retailer filter
            
        Returns:
            List of price history records
        """
        with get_db() as db:
            since_date = datetime.now() - timedelta(days=days)
            
            query = db.query(PriceHistory).filter(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.timestamp >= since_date
                )
            )
            
            if retailer:
                query = query.filter(PriceHistory.retailer == retailer)
            
            history = query.order_by(PriceHistory.timestamp).all()
            
            return [
                {
                    "retailer": h.retailer,
                    "amount": h.amount,
                    "currency": h.currency,
                    "availability": h.availability,
                    "timestamp": h.timestamp
                }
                for h in history
            ]
    
    def get_price_alert_threshold(
        self,
        product_id: str,
        percentile: float = 0.25
    ) -> Optional[float]:
        """
        Calculate a good price alert threshold based on historical data.
        
        Args:
            product_id: Product ID
            percentile: Percentile for threshold (0.25 = 25th percentile)
            
        Returns:
            Suggested price threshold
        """
        history = self.get_price_history(product_id, days=90)
        
        if not history:
            return None
        
        prices = [h["amount"] for h in history]
        prices.sort()
        
        index = int(len(prices) * percentile)
        return prices[index] if index < len(prices) else prices[0]
    
    def find_best_deals(
        self,
        category: Optional[str] = None,
        min_discount: float = 0.2,
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Find products with significant discounts.
        
        Args:
            category: Optional category filter
            min_discount: Minimum discount percentage (0.2 = 20%)
            limit: Maximum results
            
        Returns:
            List of products with best deals
        """
        with get_db() as db:
            # This is a simplified version
            # In production, you'd compare current price vs historical average
            query = db.query(DBProduct)
            
            if category:
                query = query.filter(DBProduct.category == category)
            
            products = query.limit(limit * 2).all()
            
            deals = []
            for product in products:
                comparison = self.compare_prices(product.id)
                if comparison["price_range"] and comparison["best_price"]:
                    discount_pct = (comparison["price_range"][1] - comparison["best_price"].amount) / comparison["price_range"][1]
                    if discount_pct >= min_discount:
                        deals.append({
                            "product": product,
                            "comparison": comparison,
                            "discount_percentage": discount_pct
                        })
            
            deals.sort(key=lambda x: x["discount_percentage"], reverse=True)
            return deals[:limit]
