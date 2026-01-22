# Changelog

All notable changes to the EBT Eligibility Classification System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-22

### Added
- **LLM-powered product search**: Search suggestions now generated dynamically by local LLM (Ollama) instead of static data
- **Search-first UI**: Redesigned classification page with search bar at top for quick product lookup
- **USDA FoodData Central integration**: Primary search source when API key is configured
- **Ollama local LLM support**: Run classifications entirely offline with local models (llama3.2, qwen2.5, etc.)
- **OpenAI-compatible API support**: Connect to any OpenAI-compatible LLM API (OpenRouter, local servers, etc.)
- **Quick Test Products**: Pre-configured test buttons for common product types (milk, energy drinks, vitamins, beer)

### Changed
- **Improved UX flow**: Click search result to select product, then classify with one button
- **Collapsed advanced options**: Product attributes (hot, alcohol, tobacco) hidden by default in expander
- **Made RAG dependencies optional**: ChromaDB and sentence-transformers no longer required for basic functionality
- **Better session state management**: Fixed race conditions in Streamlit product selection

### Fixed
- Quick Test Products buttons now properly update form state using widget keys
- Streamlit import path issues resolved
- Search fallback behavior when USDA API not configured
- Data sources display now shows actual LLM provider (was hardcoded to "Gemini AI")

## [1.0.0] - 2026-01-21

### Added
- Initial implementation of EBT Eligibility Classification System
- FastAPI backend with classification endpoints
- Streamlit web UI for product classification
- LangChain-based reasoning engine with multi-step analysis
- Rule-based classification for SNAP eligibility
- Support for product attributes (hot food, alcohol, tobacco, supplements, CBD)
- Classification caching in SQLite database
- Structured logging with JSON output
- Health check and audit endpoints
- Manual product entry form
- Result display with confidence scores
- Reasoning chain visualization

### Technical
- Python 3.11+ support
- Async/await throughout API layer
- Pydantic models for request/response validation
- Modular architecture with separation of concerns
