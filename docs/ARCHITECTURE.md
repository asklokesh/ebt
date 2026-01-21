# EBT Eligibility Classification System - Architecture

## Overview

The EBT Eligibility Classification System is designed as a modular, layered architecture that separates concerns between data access, business logic, and presentation. The system combines rule-based validation for deterministic cases with AI-powered reasoning for ambiguous products.

## Architecture Diagram

```
+------------------+     +------------------+
|   Streamlit UI   |     |   External Apps  |
+--------+---------+     +--------+---------+
         |                        |
         v                        v
+--------------------------------------------------+
|                    FastAPI Layer                  |
|  /classify  /explain  /challenge  /audit-trail   |
+--------------------------------------------------+
         |
         v
+--------------------------------------------------+
|              Classification Engine                |
|  - Rule Validator (deterministic cases)          |
|  - AI Reasoning Agent (ambiguous cases)          |
|  - Confidence Scorer                             |
+--------------------------------------------------+
         |
    +----+----+
    |         |
    v         v
+-------+  +------------------+
|  RAG  |  |  External APIs   |
| System|  | - USDA FoodData  |
+---+---+  | - Open Food Facts|
    |      +------------------+
    v
+------------------+
|    ChromaDB      |
| (Vector Store)   |
+------------------+
         |
         v
+------------------+
|     SQLite       |
|   (Audit Trail)  |
+------------------+
```

## Layer Architecture

### 1. Presentation Layer

**FastAPI Routes** (`src/api/routes/`)
- RESTful API endpoints
- Request validation using Pydantic
- Error handling and response formatting

**Streamlit UI** (`ui/`)
- Interactive demo interface
- Real-time classification
- Audit trail viewer
- Challenge workflow

### 2. Service Layer

**Classification Engine** (`src/services/classification_engine.py`)
- Orchestrates the classification process
- Manages caching and deduplication
- Coordinates between rule validator and AI agent

**Rule Validator** (`src/services/rule_validator.py`)
- Implements deterministic SNAP eligibility rules
- Handles clear-cut cases without AI
- Returns regulation citations

**AI Reasoning Agent** (`src/services/ai_reasoning_agent.py`)
- Processes ambiguous products
- Uses RAG for context-aware decisions
- Provides explainable reasoning chains

**Confidence Scorer** (`src/services/confidence_scorer.py`)
- Calculates confidence scores
- Considers data completeness
- Weights rule-based vs AI decisions

### 3. RAG (Retrieval-Augmented Generation) Layer

**Document Loader** (`src/rag/document_loader.py`)
- Loads SNAP regulation documents
- Splits documents into chunks
- Extracts metadata

**Vector Store** (`src/rag/vector_store.py`)
- ChromaDB for semantic search
- HuggingFace embeddings (all-MiniLM-L6-v2)
- Persistent storage

**Retriever** (`src/rag/retriever.py`)
- Semantic search for relevant regulations
- Context building for AI agent
- Relevance scoring

### 4. Data Layer

**Database** (`src/data/database.py`)
- SQLite with aiosqlite for async operations
- Connection pooling
- Transaction management

**Repositories** (`src/data/repositories/`)
- `ProductRepository`: Product data CRUD
- `ClassificationRepository`: Classification results
- `AuditRepository`: Audit trail records

**External APIs** (`src/data/external/`)
- USDA FoodData Central integration
- Open Food Facts integration
- SNAP Guidelines service

### 5. Core Layer

**Configuration** (`src/core/config.py`)
- Environment-based settings
- Pydantic Settings management

**Constants** (`src/core/constants.py`)
- Classification categories
- Threshold values
- Eligible category lists

**Exceptions** (`src/core/exceptions.py`)
- Custom exception hierarchy
- Error codes and messages

## Data Flow

### Classification Flow

```
1. Request received at /classify endpoint
   |
2. Request validation (Pydantic)
   |
3. Check cache for existing classification
   |
   +-- Cache hit --> Return cached result
   |
   +-- Cache miss --> Continue
   |
4. Rule-based validation
   |
   +-- Deterministic (clear-cut case)
   |   |
   |   +-- Return rule-based result with citations
   |
   +-- Ambiguous (needs AI)
       |
5. RAG retrieval (find relevant regulations)
   |
6. AI reasoning agent processes product
   |
7. Confidence scoring
   |
8. Store result in database
   |
9. Create audit record
   |
10. Return classification result
```

### Challenge Flow

```
1. Challenge request with audit_id
   |
2. Retrieve original classification
   |
3. Merge additional evidence with product data
   |
4. Re-run classification engine
   |
5. Compare results
   |
6. Update audit record with challenge info
   |
7. Return comparison result
```

## Key Design Decisions

### 1. Rule-Based First

The system prioritizes rule-based validation because:
- SNAP regulations have clear-cut rules for many categories
- Rule-based decisions are faster and more reliable
- Reduces AI API costs
- Provides deterministic, auditable results

### 2. Confidence Scoring

Confidence is calculated based on:
- **Data completeness** (25%): How complete is the product information
- **Rule-based certainty** (30%): Was this a clear-cut rule case
- **AI consistency** (25%): Quality of AI reasoning
- **Evidence quality** (20%): Citations and reasoning depth

### 3. Explainability

Every classification includes:
- Step-by-step reasoning chain
- Regulation citations with excerpts
- Key factors that influenced the decision
- Data sources used

### 4. Audit Trail

Complete audit trail for:
- Regulatory compliance
- Challenge resolution
- System debugging
- Analytics and reporting

## Scalability Considerations

### Current Architecture (SQLite + Local ChromaDB)

Suitable for:
- Development and testing
- Single-server deployments
- Low to moderate traffic

### Production Scaling Options

**Database**:
- PostgreSQL with asyncpg
- Connection pooling (pgbouncer)
- Read replicas for audit queries

**Vector Store**:
- Hosted ChromaDB
- Pinecone or Weaviate
- Redis with vector search

**Caching**:
- Redis for classification cache
- CDN for static assets

**API**:
- Multiple uvicorn workers
- Kubernetes deployment
- Load balancing

## Security Considerations

### Current Implementation

- Input validation via Pydantic
- SQL injection prevention (parameterized queries)
- Structured logging (no PII in logs)

### Production Recommendations

- API authentication (API keys, OAuth)
- Rate limiting
- HTTPS enforcement
- Secret management (Vault, AWS Secrets Manager)
- Audit log encryption
- Data retention policies

## Monitoring and Observability

### Logging

- Structured JSON logging (structlog)
- Request tracing with correlation IDs
- Performance metrics in logs

### Recommended Additions

- Prometheus metrics endpoint
- Grafana dashboards
- Alert rules for:
  - High error rates
  - Slow response times
  - Low confidence classifications
  - AI service failures

## Extension Points

### Adding New Rules

1. Add category to `ClassificationCategory` enum
2. Implement rule in `RuleValidator.validate()`
3. Add regulation citation
4. Add tests

### Adding New Data Sources

1. Create client in `src/data/external/`
2. Integrate in classification engine
3. Add to data sources tracking

### Adding New AI Models

1. Create new agent class
2. Implement `reason()` method
3. Configure in settings
4. Add fallback handling
