from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from database.database import get_db
from database.models import Product as DBProduct, PriceHistory


class InventoryCheckTool:
    """
    Tool for checking product availability and stock across retailers.
    """
    
    def check_availability(
        self,
        product_id: str,
        retailer: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Check product availability across retailers.
        
        Args:
            product_id: Product ID to check
            retailer: Optional specific retailer to check
            
        Returns:
            Dictionary with availability information
        """
        with get_db() as db:
            product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Get latest price/availability data
            query = db.query(PriceHistory).filter(PriceHistory.product_id == product_id)
            
            if retailer:
                query = query.filter(PriceHistory.retailer == retailer)
            
            # Get most recent entry per retailer
            latest_records = []
            retailers_seen = set()
            
            for record in query.order_by(PriceHistory.timestamp.desc()).all():
                if record.retailer not in retailers_seen:
                    latest_records.append(record)
                    retailers_seen.add(record.retailer)
            
            availability_data = []
            total_stock = 0
            available_retailers = []
            
            for record in latest_records:
                availability_data.append({
                    "retailer": record.retailer,
                    "in_stock": record.availability,
                    "stock_count": record.stock_count,
                    "price": record.amount,
                    "currency": record.currency,
                    "last_updated": record.timestamp
                })
                
                if record.availability:
                    available_retailers.append(record.retailer)
                    if record.stock_count:
                        total_stock += record.stock_count
            
            return {
                "product_id": product_id,
                "product_name": product.name,
                "availability": availability_data,
                "total_stock_count": total_stock if total_stock > 0 else None,
                "available_at": available_retailers,
                "availability_rate": len(available_retailers) / len(availability_data) if availability_data else 0
            }
    
    def check_bulk_availability(
        self,
        product_ids: List[str]
    ) -> Dict[str, Dict[str, any]]:
        """
        Check availability for multiple products.
        """
        results = {}
        for product_id in product_ids:
            try:
                results[product_id] = self.check_availability(product_id)
            except Exception as e:
                results[product_id] = {"error": str(e)}
        return results
    
    def find_in_stock_alternatives(
        self,
        product_id: str,
        max_results: int = 5
    ) -> List[Dict[str, any]]:
        """
        Find in-stock alternatives if product is out of stock.
        """
        from .product_search import ProductSearchTool
        
        availability = self.check_availability(product_id)
        
        # If product is available somewhere, return it
        if availability["available_at"]:
            return [availability]
        
        # Find similar products that are in stock
        with get_db() as db:
            product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
            if not product:
                return []
            
            search_tool = ProductSearchTool()
            similar_products = search_tool.search_similar(product_id, max_results=max_results * 2)
            
            # Filter to only in-stock products
            in_stock_alternatives = []
            for similar in similar_products:
                alt_availability = self.check_availability(similar.product.id)
                if alt_availability["available_at"]:
                    in_stock_alternatives.append({
                        "product": similar.product,
                        "match_score": similar.match_score,
                        "availability": alt_availability
                    })
            
            return in_stock_alternatives[:max_results]
    
    def get_stock_alerts(
        self,
        threshold: int = 5
    ) -> List[Dict[str, any]]:
        """
        Get products with low stock.
        
        Args:
            threshold: Stock count threshold
            
        Returns:
            List of products with low stock
        """
        with get_db() as db:
            low_stock = db.query(PriceHistory).filter(
                and_(
                    PriceHistory.availability == True,
                    PriceHistory.stock_count <= threshold,
                    PriceHistory.stock_count > 0
                )
            ).order_by(PriceHistory.stock_count).all()
            
            alerts = []
            seen_products = set()
            
            for record in low_stock:
                if record.product_id not in seen_products:
                    alerts.append({
                        "product_id": record.product_id,
                        "product_name": record.product.name,
                        "retailer": record.retailer,
                        "stock_count": record.stock_count,
                        "last_updated": record.timestamp
                    })
                    seen_products.add(record.product_id)
            
            return alerts
    
    def estimate_restock_time(
        self,
        product_id: str,
        retailer: str
    ) -> Optional[Dict[str, any]]:
        """
        Estimate when product will be back in stock based on historical patterns.
        This is a simplified version - production would use ML models.
        """
        with get_db() as db:
            # Get historical availability changes
            history = db.query(PriceHistory).filter(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.retailer == retailer
                )
            ).order_by(PriceHistory.timestamp).all()
            
            if len(history) < 2:
                return None
            
            # Find patterns of going out of stock and back in stock
            out_of_stock_periods = []
            last_in_stock = None
            went_out_of_stock = None
            
            for record in history:
                if record.availability and went_out_of_stock:
                    # Came back in stock
                    out_of_stock_periods.append(
                        (record.timestamp - went_out_of_stock).days
                    )
                    went_out_of_stock = None
                elif not record.availability and not went_out_of_stock:
                    # Went out of stock
                    went_out_of_stock = record.timestamp
            
            if not out_of_stock_periods:
                return None
            
            # Calculate average restock time
            avg_days = sum(out_of_stock_periods) / len(out_of_stock_periods)
            
            return {
                "estimated_days": int(avg_days),
                "confidence": "low" if len(out_of_stock_periods) < 3 else "medium",
                "based_on_samples": len(out_of_stock_periods)
            }
