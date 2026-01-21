#!/usr/bin/env python3
"""Build the ChromaDB vector store from regulation documents."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.document_loader import DocumentLoader
from src.rag.vector_store import VectorStore


def main() -> None:
    """Build the vector store."""
    print("Building SNAP regulations vector store...")

    # Initialize components
    loader = DocumentLoader()
    vector_store = VectorStore()

    # Check if collection already has documents
    existing_count = vector_store.count
    if existing_count > 0:
        print(f"Collection already has {existing_count} documents.")
        response = input("Delete and rebuild? (y/n): ").strip().lower()
        if response == "y":
            vector_store.delete_collection()
            print("Collection deleted.")
        else:
            print("Keeping existing collection.")
            return

    # Load and chunk documents
    print("Loading regulation documents...")
    chunks = loader.load_and_chunk_all(chunk_size=1000, overlap=200)

    if not chunks:
        print("No documents found in data/regulations/")
        print("Please add regulation text files before building the vector store.")
        return

    print(f"Loaded {len(chunks)} document chunks.")

    # Prepare for insertion
    documents = [chunk.content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    ids = [chunk.doc_id for chunk in chunks]

    # Add to vector store
    print("Adding documents to vector store...")
    vector_store.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

    # Verify
    final_count = vector_store.count
    print(f"Vector store built successfully with {final_count} documents.")

    # Test query
    print("\nTesting retrieval...")
    test_query = "SNAP eligibility for alcoholic beverages"
    results = vector_store.query(test_query, n_results=2)

    print(f"Query: '{test_query}'")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Source: {result['metadata'].get('source', 'Unknown')}")
        print(f"    Distance: {result['distance']:.4f}")
        print(f"    Preview: {result['document'][:100]}...")


if __name__ == "__main__":
    main()
