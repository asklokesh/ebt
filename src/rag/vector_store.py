"""ChromaDB vector store integration (optional)."""

from typing import Any, List, Optional

from src.core.config import settings
from src.core.exceptions import VectorStoreError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import chromadb, but make it optional
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb_not_available", message="ChromaDB not installed, RAG features disabled")


class VectorStore:
    """ChromaDB vector store for SNAP regulations."""

    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = None,
        embeddings: Any = None,
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
        self._embeddings = embeddings
        self._client = None
        self._collection = None
        self._available = CHROMADB_AVAILABLE

    @property
    def embeddings(self):
        """Lazy load embeddings."""
        if self._embeddings is None and self._available:
            try:
                from src.rag.embeddings import get_embeddings
                self._embeddings = get_embeddings()
            except Exception as e:
                logger.warning("embeddings_load_failed", error=str(e))
                self._available = False
        return self._embeddings

    @property
    def is_available(self) -> bool:
        """Check if vector store is available."""
        return self._available and CHROMADB_AVAILABLE

    @property
    def client(self):
        """Get or create ChromaDB client."""
        if not self.is_available:
            return None

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
                self._available = False
                return None
        return self._client

    @property
    def collection(self):
        """Get or create the collection."""
        if not self.is_available or self.client is None:
            return None

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
                self._available = False
                return None
        return self._collection

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to the vector store."""
        if not self.is_available or not documents:
            return

        try:
            embeddings = self.embeddings.embed_texts(documents)
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]

            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info("documents_added", count=len(documents))
        except Exception as e:
            logger.error("add_documents_failed", error=str(e))

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> List[dict]:
        """Query the vector store."""
        if not self.is_available:
            return []

        try:
            query_embedding = self.embeddings.embed_text(query_text)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

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

            return formatted_results
        except Exception as e:
            logger.error("query_failed", error=str(e))
            return []

    def delete_collection(self) -> None:
        """Delete the current collection."""
        if not self.is_available:
            return
        try:
            self.client.delete_collection(self.collection_name)
            self._collection = None
        except Exception as e:
            logger.error("delete_collection_failed", error=str(e))

    def reset(self) -> None:
        """Reset the entire database."""
        if not self.is_available:
            return
        try:
            self.client.reset()
            self._collection = None
        except Exception as e:
            logger.error("reset_failed", error=str(e))

    @property
    def count(self) -> int:
        """Get the number of documents in the collection."""
        if not self.is_available or self.collection is None:
            return 0
        return self.collection.count()


# Global vector store instance
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
