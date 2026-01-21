"""HuggingFace sentence-transformers embeddings."""

from typing import List

from src.core.config import settings
from src.core.exceptions import EmbeddingError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingsManager:
    """Manages text embeddings using sentence-transformers."""

    def __init__(self, model_name: str = None):
        """
        Initialize embeddings manager.

        Args:
            model_name: Name of the sentence-transformer model
        """
        self.model_name = model_name or settings.embedding_model
        self._model = None

    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("loading_embedding_model", model=self.model_name)
                self._model = SentenceTransformer(self.model_name)
                logger.info("embedding_model_loaded", model=self.model_name)
            except Exception as e:
                logger.error("embedding_model_load_failed", error=str(e))
                raise EmbeddingError(f"Failed to load embedding model: {e}")
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error("embedding_failed", error=str(e), text_length=len(text))
            raise EmbeddingError(f"Failed to generate embedding: {e}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error("batch_embedding_failed", error=str(e), count=len(texts))
            raise EmbeddingError(f"Failed to generate embeddings: {e}")

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        return self.model.get_sentence_embedding_dimension()


# Global embeddings instance
_embeddings: EmbeddingsManager | None = None


def get_embeddings() -> EmbeddingsManager:
    """Get the global embeddings manager."""
    global _embeddings
    if _embeddings is None:
        _embeddings = EmbeddingsManager()
    return _embeddings
