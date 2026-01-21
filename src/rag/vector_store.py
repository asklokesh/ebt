"""ChromaDB vector store integration."""

from typing import Any, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.core.config import settings
from src.core.exceptions import VectorStoreError
from src.rag.embeddings import EmbeddingsManager, get_embeddings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """ChromaDB vector store for SNAP regulations."""

    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = None,
        embeddings: EmbeddingsManager = None,
    ):
        """
        Initialize vector store.

        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the collection
            embeddings: Embeddings manager instance
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embeddings = embeddings or get_embeddings()
        self._client = None
        self._collection = None

    @property
    def client(self) -> chromadb.PersistentClient:
        """Get or create ChromaDB client."""
        if self._client is None:
            try:
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                    ),
                )
                logger.info(
                    "chromadb_client_created",
                    path=self.persist_directory,
                )
            except Exception as e:
                logger.error("chromadb_client_failed", error=str(e))
                raise VectorStoreError(f"Failed to create ChromaDB client: {e}")
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the collection."""
        if self._collection is None:
            try:
                self._collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "SNAP regulations and eligibility guidelines"},
                )
                logger.info(
                    "chromadb_collection_ready",
                    name=self.collection_name,
                    count=self._collection.count(),
                )
            except Exception as e:
                logger.error("chromadb_collection_failed", error=str(e))
                raise VectorStoreError(f"Failed to get/create collection: {e}")
        return self._collection

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Add documents to the vector store.

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
        """
        if not documents:
            return

        try:
            # Generate embeddings
            embeddings = self.embeddings.embed_texts(documents)

            # Generate IDs if not provided
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]

            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(
                "documents_added",
                count=len(documents),
                collection=self.collection_name,
            )
        except Exception as e:
            logger.error("add_documents_failed", error=str(e))
            raise VectorStoreError(f"Failed to add documents: {e}")

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> List[dict]:
        """
        Query the vector store.

        Args:
            query_text: Text to search for
            n_results: Number of results to return
            where: Optional filter conditions

        Returns:
            List of matching documents with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_text(query_text)

            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "document": doc,
                        "metadata": (
                            results["metadatas"][0][i]
                            if results["metadatas"] and results["metadatas"][0]
                            else {}
                        ),
                        "distance": (
                            results["distances"][0][i]
                            if results["distances"] and results["distances"][0]
                            else 0
                        ),
                        "id": (
                            results["ids"][0][i]
                            if results["ids"] and results["ids"][0]
                            else f"result_{i}"
                        ),
                    })

            logger.info(
                "query_executed",
                query_length=len(query_text),
                results_count=len(formatted_results),
            )

            return formatted_results
        except Exception as e:
            logger.error("query_failed", error=str(e))
            raise VectorStoreError(f"Failed to query vector store: {e}")

    def delete_collection(self) -> None:
        """Delete the current collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self._collection = None
            logger.info("collection_deleted", name=self.collection_name)
        except Exception as e:
            logger.error("delete_collection_failed", error=str(e))
            raise VectorStoreError(f"Failed to delete collection: {e}")

    def reset(self) -> None:
        """Reset the entire database."""
        try:
            self.client.reset()
            self._collection = None
            logger.info("vector_store_reset")
        except Exception as e:
            logger.error("reset_failed", error=str(e))
            raise VectorStoreError(f"Failed to reset vector store: {e}")

    @property
    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()


# Global vector store instance
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
