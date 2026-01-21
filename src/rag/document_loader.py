"""Document loader for SNAP regulation documents."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Document:
    """A loaded document with metadata."""

    content: str
    metadata: dict
    doc_id: str


class DocumentLoader:
    """Loads SNAP regulation documents for the vector store."""

    def __init__(self, regulations_dir: str = None):
        """
        Initialize document loader.

        Args:
            regulations_dir: Directory containing regulation documents
        """
        if regulations_dir is None:
            # Default to data/regulations relative to project root
            regulations_dir = Path(__file__).parent.parent.parent / "data" / "regulations"
        self.regulations_dir = Path(regulations_dir)

    def load_all(self) -> List[Document]:
        """
        Load all regulation documents from the directory.

        Returns:
            List of Document objects
        """
        documents = []

        if not self.regulations_dir.exists():
            logger.warning("regulations_dir_not_found", path=str(self.regulations_dir))
            return documents

        for file_path in self.regulations_dir.glob("*.txt"):
            try:
                doc = self._load_file(file_path)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.error(
                    "document_load_failed",
                    path=str(file_path),
                    error=str(e),
                )

        logger.info("documents_loaded", count=len(documents))
        return documents

    def _load_file(self, file_path: Path) -> Optional[Document]:
        """
        Load a single document file.

        Args:
            file_path: Path to the document file

        Returns:
            Document object or None
        """
        content = file_path.read_text(encoding="utf-8")

        if not content.strip():
            logger.warning("empty_document", path=str(file_path))
            return None

        # Determine document type from filename
        filename = file_path.stem
        doc_type = self._determine_doc_type(filename)
        source_url = self._get_source_url(filename)

        metadata = {
            "source": filename,
            "file_path": str(file_path),
            "doc_type": doc_type,
            "source_url": source_url,
        }

        return Document(
            content=content,
            metadata=metadata,
            doc_id=filename,
        )

    def _determine_doc_type(self, filename: str) -> str:
        """Determine document type from filename."""
        if "cfr" in filename.lower():
            return "cfr"
        elif "fns" in filename.lower():
            return "fns_policy"
        else:
            return "guidance"

    def _get_source_url(self, filename: str) -> str:
        """Get the source URL for a document."""
        url_map = {
            "cfr_7_271_2": "https://www.ecfr.gov/current/title-7/section-271.2",
            "fns_eligible_foods": "https://www.fns.usda.gov/snap/eligible-food-items",
            "fns_ineligible_items": "https://www.fns.usda.gov/snap/eligible-food-items",
        }
        return url_map.get(filename, "https://www.fns.usda.gov/snap")

    def chunk_document(
        self,
        document: Document,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> List[Document]:
        """
        Split a document into chunks for better retrieval.

        Args:
            document: Document to chunk
            chunk_size: Target size of each chunk
            overlap: Overlap between chunks

        Returns:
            List of chunked documents
        """
        content = document.content
        chunks = []

        # Split by paragraphs first
        paragraphs = content.split("\n\n")

        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunk_doc = Document(
                        content=current_chunk.strip(),
                        metadata={
                            **document.metadata,
                            "chunk_index": chunk_index,
                            "is_chunk": True,
                        },
                        doc_id=f"{document.doc_id}_chunk_{chunk_index}",
                    )
                    chunks.append(chunk_doc)
                    chunk_index += 1

                # Start new chunk with overlap
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"

        # Add final chunk
        if current_chunk:
            chunk_doc = Document(
                content=current_chunk.strip(),
                metadata={
                    **document.metadata,
                    "chunk_index": chunk_index,
                    "is_chunk": True,
                },
                doc_id=f"{document.doc_id}_chunk_{chunk_index}",
            )
            chunks.append(chunk_doc)

        logger.info(
            "document_chunked",
            doc_id=document.doc_id,
            chunks=len(chunks),
        )

        return chunks

    def load_and_chunk_all(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> List[Document]:
        """
        Load all documents and chunk them.

        Args:
            chunk_size: Target size of each chunk
            overlap: Overlap between chunks

        Returns:
            List of chunked documents
        """
        documents = self.load_all()
        all_chunks = []

        for doc in documents:
            chunks = self.chunk_document(doc, chunk_size, overlap)
            all_chunks.extend(chunks)

        logger.info(
            "all_documents_chunked",
            original_count=len(documents),
            chunk_count=len(all_chunks),
        )

        return all_chunks
