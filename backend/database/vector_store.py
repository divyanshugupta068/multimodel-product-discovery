import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI

from config import get_settings


class VectorStore:
    """
    Vector store for product embeddings using ChromaDB.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=self.settings.chroma_persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = "products"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
    
    def add_product(
        self,
        product_id: str,
        text: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ):
        """
        Add product to vector store.
        
        Args:
            product_id: Unique product identifier
            text: Product text (name + description)
            metadata: Product metadata
            embedding: Pre-computed embedding (optional)
        """
        if embedding is None:
            embedding = self.get_embedding(text)
        
        self.collection.add(
            ids=[product_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
    
    def add_products_batch(
        self,
        product_ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ):
        """Add multiple products in batch."""
        if embeddings is None:
            embeddings = self.get_embeddings_batch(texts)
        
        self.collection.add(
            ids=product_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search products by query.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filter: Metadata filter
            
        Returns:
            Dictionary with ids, distances, and metadatas
        """
        query_embedding = self.get_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter
        )
        
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else []
        }
    
    def search_by_embedding(
        self,
        embedding: List[float],
        n_results: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search products by embedding vector."""
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=filter
        )
        
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else []
        }
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        response = self.openai_client.embeddings.create(
            model=self.settings.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        response = self.openai_client.embeddings.create(
            model=self.settings.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def update_product(
        self,
        product_id: str,
        text: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ):
        """Update product in vector store."""
        if embedding is None:
            embedding = self.get_embedding(text)
        
        self.collection.update(
            ids=[product_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
    
    def delete_product(self, product_id: str):
        """Delete product from vector store."""
        self.collection.delete(ids=[product_id])
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        results = self.collection.get(ids=[product_id])
        
        if results["ids"]:
            return {
                "id": results["ids"][0],
                "document": results["documents"][0] if results["documents"] else None,
                "metadata": results["metadatas"][0] if results["metadatas"] else None
            }
        return None
    
    def clear(self):
        """Clear all products from collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def count(self) -> int:
        """Get total number of products."""
        return self.collection.count()
