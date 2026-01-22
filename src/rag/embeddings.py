"""HuggingFace sentence-transformers embeddings (optional)."""

from typing import List, Optional

from src.core.config import settings
from src.core.exceptions import EmbeddingError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import sentence_transformers, but make it optional
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence_transformers_not_available", message="sentence-transformers not installed")


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
        self._available = SENTENCE_TRANSFORMERS_AVAILABLE

    @property
    def is_available(self) -> bool:
        """Check if embeddings are available."""
        return self._available and SENTENCE_TRANSFORMERS_AVAILABLE

    @property
    def model(self):
        """Lazy load the embedding model."""
        if not self.is_available:
            return None

        if self._model is None:
            try:
                logger.info("loading_embedding_model", model=self.model_name)
                self._model = SentenceTransformer(self.model_name)
                logger.info("embedding_model_loaded", model=self.model_name)
            except Exception as e:
                logger.error("embedding_model_load_failed", error=str(e))
                self._available = False
                return None
        return self._model

    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding, or None if not available
        """
        if not self.is_available or self.model is None:
            return None

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error("embedding_failed", error=str(e), text_length=len(text))
            return None

    def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings, or None if not available
        """
        if not self.is_available or self.model is None:
            return None

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error("batch_embedding_failed", error=str(e), count=len(texts))
            return None

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        if not self.is_available or self.model is None:
            return 384  # Default for all-MiniLM-L6-v2
        return self.model.get_sentence_embedding_dimension()


# Global embeddings instance
_embeddings: EmbeddingsManager | None = None


def get_embeddings() -> EmbeddingsManager:
    """Get the global embeddings manager."""
    global _embeddings
    if _embeddings is None:
        _embeddings = EmbeddingsManager()
    return _embeddings
