"""
Script to load sample product data into the database.
Run this to populate the database with test products.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/backend")

from database.database import init_db, get_db
from database.models import Product, PriceHistory, Review
from database.vector_store import VectorStore
import uuid
from datetime import datetime, timedelta
import random


# Sample product data
SAMPLE_PRODUCTS = [
    {
        "name": "Classic Leather Jacket - Black",
        "description": "Premium black leather jacket with zipper closure, perfect for casual and formal wear. Made from genuine leather with soft inner lining.",
        "category": "clothing",
        "brand": "StyleCraft",
        "features": {
            "color": "black",
            "material": "genuine leather",
            "style": "classic",
            "size": "M"
        },
        "images": ["https://example.com/leather-jacket-1.jpg"],
        "prices": [
            {"retailer": "Amazon", "amount": 189.99, "stock": 15},
            {"retailer": "Nordstrom", "amount": 199.99, "stock": 8},
            {"retailer": "Macy's", "amount": 179.99, "stock": 12}
        ]
    },
    {
        "name": "Red Leather Jacket - Women's",
        "description": "Stylish red leather jacket for women with modern fit. Features front zipper, side pockets, and adjustable cuffs.",
        "category": "clothing",
        "brand": "FashionHub",
        "features": {
            "color": "red",
            "material": "faux leather",
            "style": "modern",
            "size": "S"
        },
        "images": ["https://example.com/red-jacket-1.jpg"],
        "prices": [
            {"retailer": "Amazon", "amount": 149.99, "stock": 20},
            {"retailer": "Zara", "amount": 159.99, "stock": 5},
            {"retailer": "H&M", "amount": 139.99, "stock": 0}
        ]
    },
    {
        "name": "iPhone 15 Pro Max - 256GB",
        "description": "Latest iPhone 15 Pro Max with A17 Pro chip, titanium design, and advanced camera system. 6.7-inch Super Retina XDR display.",
        "category": "electronics",
        "brand": "Apple",
        "features": {
            "color": "natural titanium",
            "storage": "256GB",
            "model": "iPhone 15 Pro Max"
        },
        "images": ["https://example.com/iphone15-1.jpg"],
        "prices": [
            {"retailer": "Apple Store", "amount": 1199.99, "stock": 50},
            {"retailer": "Best Buy", "amount": 1199.99, "stock": 30},
            {"retailer": "Amazon", "amount": 1189.99, "stock": 25}
        ]
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "description": "Samsung's flagship phone with 200MP camera, S Pen, and powerful Snapdragon processor. 6.8-inch Dynamic AMOLED display.",
        "category": "electronics",
        "brand": "Samsung",
        "features": {
            "color": "titanium gray",
            "storage": "512GB",
            "model": "S24 Ultra"
        },
        "images": ["https://example.com/s24-1.jpg"],
        "prices": [
            {"retailer": "Samsung", "amount": 1299.99, "stock": 40},
            {"retailer": "Best Buy", "amount": 1299.99, "stock": 35},
            {"retailer": "Amazon", "amount": 1279.99, "stock": 20}
        ]
    },
    {
        "name": "Running Shoes - Nike Air Zoom Pegasus 40",
        "description": "Lightweight running shoes with responsive cushioning. Perfect for daily runs and training.",
        "category": "sports",
        "brand": "Nike",
        "features": {
            "color": "white/black",
            "size": "10",
            "style": "athletic"
        },
        "images": ["https://example.com/nike-pegasus-1.jpg"],
        "prices": [
            {"retailer": "Nike", "amount": 129.99, "stock": 60},
            {"retailer": "Foot Locker", "amount": 129.99, "stock": 45},
            {"retailer": "Dick's", "amount": 119.99, "stock": 30}
        ]
    },
    {
        "name": "Wireless Noise Cancelling Headphones",
        "description": "Premium wireless headphones with active noise cancellation, 30-hour battery life, and premium sound quality.",
        "category": "electronics",
        "brand": "Sony",
        "features": {
            "color": "black",
            "model": "WH-1000XM5",
            "connectivity": "Bluetooth 5.2"
        },
        "images": ["https://example.com/sony-headphones-1.jpg"],
        "prices": [
            {"retailer": "Best Buy", "amount": 399.99, "stock": 25},
            {"retailer": "Amazon", "amount": 379.99, "stock": 40},
            {"retailer": "Sony", "amount": 399.99, "stock": 15}
        ]
    },
    {
        "name": "Yoga Mat - Extra Thick",
        "description": "Premium yoga mat with extra cushioning, non-slip surface, and eco-friendly materials. Perfect for yoga, pilates, and stretching.",
        "category": "sports",
        "brand": "Gaiam",
        "features": {
            "color": "purple",
            "thickness": "6mm",
            "material": "TPE"
        },
        "images": ["https://example.com/yoga-mat-1.jpg"],
        "prices": [
            {"retailer": "Amazon", "amount": 29.99, "stock": 100},
            {"retailer": "Target", "amount": 34.99, "stock": 75},
            {"retailer": "Dick's", "amount": 32.99, "stock": 50}
        ]
    },
    {
        "name": "Stainless Steel Water Bottle - 32oz",
        "description": "Insulated stainless steel water bottle keeps drinks cold for 24 hours or hot for 12 hours. Leak-proof lid.",
        "category": "sports",
        "brand": "Hydro Flask",
        "features": {
            "color": "blue",
            "capacity": "32oz",
            "material": "stainless steel"
        },
        "images": ["https://example.com/water-bottle-1.jpg"],
        "prices": [
            {"retailer": "Amazon", "amount": 44.95, "stock": 80},
            {"retailer": "REI", "amount": 44.95, "stock": 60},
            {"retailer": "Target", "amount": 39.99, "stock": 45}
        ]
    }
]


def load_sample_data():
    """Load sample product data into database."""
    print("Initializing database...")
    init_db()
    
    print("Initializing vector store...")
    vector_store = VectorStore()
    
    print(f"Loading {len(SAMPLE_PRODUCTS)} sample products...")
    
    with get_db() as db:
        for product_data in SAMPLE_PRODUCTS:
            product_id = str(uuid.uuid4())
            
            # Create product
            product = Product(
                id=product_id,
                name=product_data["name"],
                description=product_data["description"],
                category=product_data["category"],
                brand=product_data.get("brand"),
                features=product_data.get("features", {}),
                images=product_data.get("images", [])
            )
            db.add(product)
            
            # Add prices
            for price_data in product_data.get("prices", []):
                price = PriceHistory(
                    product_id=product_id,
                    retailer=price_data["retailer"],
                    amount=price_data["amount"],
                    currency="USD",
                    availability=price_data.get("stock", 0) > 0,
                    stock_count=price_data.get("stock")
                )
                db.add(price)
            
            # Add sample reviews
            for i in range(random.randint(5, 15)):
                rating = random.choice([3, 3, 4, 4, 4, 5, 5, 5])
                review = Review(
                    product_id=product_id,
                    rating=float(rating),
                    title=f"Review {i+1}",
                    content=f"Sample review content for {product_data['name']}. " * random.randint(2, 5),
                    sentiment_score=random.uniform(0.3, 1.0) if rating >= 4 else random.uniform(-0.5, 0.3),
                    helpful_count=random.randint(0, 50),
                    verified_purchase=random.choice([True, True, False]),
                    created_at=datetime.now() - timedelta(days=random.randint(1, 365))
                )
                db.add(review)
            
            # Add to vector store
            text_for_embedding = f"{product_data['name']} {product_data['description']}"
            metadata = {
                "category": product_data["category"],
                "brand": product_data.get("brand", ""),
                "name": product_data["name"]
            }
            
            vector_store.add_product(
                product_id=product_id,
                text=text_for_embedding,
                metadata=metadata
            )
            
            print(f"  ✓ Loaded: {product_data['name']}")
    
    print(f"\n✓ Successfully loaded {len(SAMPLE_PRODUCTS)} products!")
    print(f"✓ Vector store now contains {vector_store.count()} products")
    print("\nYou can now start the API server with:")
    print("  cd backend && python -m uvicorn api.main:app --reload")


if __name__ == "__main__":
    load_sample_data()
