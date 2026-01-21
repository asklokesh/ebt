# Product Requirements Document (PRD)
## EBT Eligibility Classification System

**Version:** 1.0  
**Date:** January 21, 2026  
**Team:** Loki Agents (HTC Global Services - CS BU Hackathon 2026)  
**Primary Contact:** Padma  
**Team Members:** Lokesh Mure, [Team Member 2], [Team Member 3], [Team Member 4]

---

## 1. Executive Summary

### 1.1 Problem Statement
Retailers must accurately classify products for SNAP/EBT (Supplemental Nutrition Assistance Program / Electronic Benefits Transfer) eligibility to ensure regulatory compliance and accurate checkout processing. Manual classification is error-prone, time-consuming, and fails to scale across large product catalogs. Misclassification results in compliance violations, checkout failures, revenue loss, and potential federal penalties.

### 1.2 Solution Overview
An AI-powered classification system that automatically determines EBT eligibility for retail products by applying USDA SNAP guidelines (7 CFR § 271.2) through a reasoning agent. The system provides explainable decisions with regulatory citations, supports bulk catalog processing, and maintains complete audit trails for compliance verification.

### 1.3 Key Differentiators
- **100% Free Stack:** No paid APIs or cloud costs
- **Explainability:** Full reasoning traces citing specific USDA SNAP regulations
- **Auditability:** Complete decision audit trail for compliance
- **Batch Processing:** Catalog-wide classification capability
- **Challenge Workflow:** Dispute resolution with agent re-evaluation

---

## 2. Regulatory Foundation

### 2.1 Governing Regulations
The system must implement classification rules based on:
- **Primary:** 7 CFR § 271.2 (Code of Federal Regulations - SNAP Definitions)
- **Secondary:** Section 3(k) of the Food and Nutrition Act of 2008
- **Guidance:** FNS (Food and Nutrition Service) Policy Memoranda

### 2.2 EBT Eligible Items (SNAP-Purchasable)
Items that CAN be purchased with SNAP benefits:

| Category | Examples | Notes |
|----------|----------|-------|
| Staple Foods - Meat/Poultry/Fish | Beef, chicken, fish, pork, lamb | Fresh, frozen, or canned |
| Staple Foods - Bread/Cereals | Bread, rice, pasta, cereal, flour | Includes gluten-free alternatives |
| Staple Foods - Vegetables/Fruits | Fresh, frozen, canned produce | Includes 100% fruit/vegetable juice |
| Staple Foods - Dairy | Milk, cheese, yogurt, butter | Includes plant-based alternatives (soy, almond, oat milk) |
| Snack Foods | Chips, candy, cookies, ice cream | Eligible despite not being nutritious |
| Non-Alcoholic Beverages | Soda, coffee, tea, juice | Must have Nutrition Facts label |
| Seeds and Plants | Vegetable seeds, fruit-producing plants | Must produce food for consumption |
| Cooking Ingredients | Oils, spices, baking supplies, pectin | For home food preparation |
| Baby Food/Formula | Infant formula, baby cereals, baby food | All varieties |
| Water and Ice | Bottled water, bags of ice | Eligible for purchase |
| Cold Prepared Foods | Deli sandwiches, cold pizza, salads | NOT hot at point of sale |

### 2.3 EBT Ineligible Items (NOT SNAP-Purchasable)
Items that CANNOT be purchased with SNAP benefits:

| Category | Examples | Regulatory Basis |
|----------|----------|------------------|
| Alcoholic Beverages | Beer, wine, liquor, dealcoholized wine | Explicitly excluded by statute |
| Tobacco Products | Cigarettes, cigars, chewing tobacco, e-cigarettes, vape products | Explicitly excluded by statute |
| Hot Foods | Rotisserie chicken, hot pizza, hot soup, hot coffee | 7 CFR § 271.2 - not for home preparation |
| Foods for On-Premises Consumption | Restaurant meals, food court items | Unless authorized meal program |
| Vitamins/Supplements | Vitamins, dietary supplements, protein powders with Supplement Facts label | Has Supplement Facts label (not Nutrition Facts) |
| Medicines | OTC drugs, prescription medications | Non-food items |
| Non-Food Items | Pet food, cleaning supplies, paper products, cosmetics, hygiene items | Not intended for human consumption |
| Live Animals | Live chickens, live cattle | Exception: shellfish, fish removed from water, animals slaughtered before pickup |
| Cannabis/CBD Products | CBD-infused foods, marijuana edibles | Controlled substances |
| Household Items | Soap, detergent, toilet paper | Non-food |
| Prepared Foods with >50% Hot Sales | "You buy, we fry" items | Restaurant threshold rule |

### 2.4 Classification Decision Rules

```
DECISION TREE:
1. Is it intended for human consumption?
   NO → INELIGIBLE (non-food item)
   YES → Continue

2. Does it contain alcohol (>0.5% ABV)?
   YES → INELIGIBLE (alcoholic beverage)
   NO → Continue

3. Is it a tobacco or nicotine product?
   YES → INELIGIBLE (tobacco product)
   NO → Continue

4. Does it have a Supplement Facts label?
   YES → INELIGIBLE (supplement/vitamin)
   NO → Continue

5. Is it hot at the point of sale?
   YES → INELIGIBLE (hot food)
   NO → Continue

6. Is it intended for on-premises consumption?
   YES → INELIGIBLE (restaurant food)
   NO → Continue

7. Does it contain cannabis/CBD/controlled substances?
   YES → INELIGIBLE (controlled substance)
   NO → Continue

8. Is it a medicine or pharmaceutical?
   YES → INELIGIBLE (medicine)
   NO → Continue

9. Is it a live animal (not shellfish/fish removed from water)?
   YES → INELIGIBLE (live animal)
   NO → ELIGIBLE
```

---

## 3. Technical Architecture

### 3.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EBT Classification System                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────────────────────────────────────────┐   │
│  │   Streamlit  │    │                  FastAPI Backend                  │   │
│  │   Frontend   │◄──►│  /classify  /bulk-classify  /explain  /audit     │   │
│  │  (Demo UI)   │    │                                                    │   │
│  └──────────────┘    └─────────────────────┬────────────────────────────┘   │
│                                            │                                 │
│                                            ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Classification Engine                             │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │    │
│  │  │  Rule-Based     │  │  AI Reasoning   │  │  Confidence         │ │    │
│  │  │  Validator      │◄─┤  Agent (Gemini) │──┤  Scorer             │ │    │
│  │  │  (CFR 7 §271.2) │  │  + LangChain    │  │                     │ │    │
│  │  └─────────────────┘  └────────┬────────┘  └─────────────────────┘ │    │
│  └────────────────────────────────┼────────────────────────────────────┘    │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Knowledge Layer                                 │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │    │
│  │  │  ChromaDB       │  │  SQLite         │  │  SNAP Regulations   │ │    │
│  │  │  Vector Store   │  │  Product DB     │  │  Embedded Docs      │ │    │
│  │  │  (Embeddings)   │  │  + Audit Trail  │  │  (fns.usda.gov)     │ │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    External Data Sources (Free APIs)                 │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │    │
│  │  │  USDA FoodData  │  │  Open Food      │  │  USDA SNAP          │ │    │
│  │  │  Central API    │  │  Facts API      │  │  Retailer API       │ │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

| Layer | Technology | Purpose | Cost |
|-------|------------|---------|------|
| **AI/LLM** | Google Gemini API (free tier) | Reasoning + Classification | Free (15 RPM, 1M tokens/day) |
| **AI/LLM Fallback** | Ollama + Llama 3.1 | Local inference fallback | Free (local) |
| **Agent Framework** | LangChain (Python) | Agent orchestration | Free (open-source) |
| **Vector Store** | ChromaDB | Semantic search on regulations | Free (open-source) |
| **Embeddings** | HuggingFace sentence-transformers (all-MiniLM-L6-v2) | Text embeddings | Free (open-source) |
| **Database** | SQLite | Product catalog + Audit trail | Free |
| **Backend API** | FastAPI | REST API endpoints | Free (open-source) |
| **Frontend** | Streamlit | Demo UI | Free (Streamlit Community Cloud) |
| **Logging** | structlog | JSON-formatted logs | Free (open-source) |
| **Deployment** | Render.com / Railway (free tier) | API hosting | Free |

### 3.3 External Data Sources

| Source | URL | Purpose | Rate Limits |
|--------|-----|---------|-------------|
| USDA FoodData Central | https://fdc.nal.usda.gov/api-guide.html | Product nutrition/categories | Free API key required |
| Open Food Facts | https://world.openfoodfacts.org/data | Product database | Unlimited |
| USDA SNAP Guidelines | https://fns.usda.gov | Regulation documents | Static (scraped) |
| USDA SNAP Retailer API | https://www.fns.usda.gov/snap/retailer-locator | Retailer data | Free |

---

## 4. Data Models

### 4.1 Product Input Schema

```python
class ProductInput(BaseModel):
    """Input schema for product classification request"""
    product_id: str                    # Unique identifier (UPC, SKU, or internal ID)
    product_name: str                  # Human-readable product name
    description: Optional[str]         # Product description
    category: Optional[str]            # Product category (e.g., "Beverages", "Snacks")
    brand: Optional[str]               # Brand name
    upc: Optional[str]                 # Universal Product Code
    ingredients: Optional[List[str]]   # List of ingredients
    nutrition_label_type: Optional[Literal["nutrition_facts", "supplement_facts", "none"]]
    is_hot_at_sale: Optional[bool]     # Is product hot at point of sale
    is_for_onsite_consumption: Optional[bool]  # Intended for on-premises consumption
    alcohol_content: Optional[float]   # Alcohol by volume (0.0 - 1.0)
    contains_tobacco: Optional[bool]   # Contains tobacco/nicotine
    contains_cbd_cannabis: Optional[bool]  # Contains CBD or cannabis
    is_live_animal: Optional[bool]     # Is a live animal
    additional_attributes: Optional[Dict[str, Any]]  # Extensible attributes
```

### 4.2 Classification Result Schema

```python
class ClassificationResult(BaseModel):
    """Output schema for classification result"""
    product_id: str
    product_name: str
    
    # Classification
    is_ebt_eligible: bool
    confidence_score: float            # 0.0 - 1.0
    classification_category: Literal[
        "ELIGIBLE_STAPLE_FOOD",
        "ELIGIBLE_SNACK_FOOD",
        "ELIGIBLE_BEVERAGE",
        "ELIGIBLE_COOKING_INGREDIENT",
        "ELIGIBLE_BABY_FOOD",
        "ELIGIBLE_SEEDS_PLANTS",
        "ELIGIBLE_OTHER",
        "INELIGIBLE_ALCOHOL",
        "INELIGIBLE_TOBACCO",
        "INELIGIBLE_HOT_FOOD",
        "INELIGIBLE_ONSITE_CONSUMPTION",
        "INELIGIBLE_SUPPLEMENT",
        "INELIGIBLE_MEDICINE",
        "INELIGIBLE_NON_FOOD",
        "INELIGIBLE_LIVE_ANIMAL",
        "INELIGIBLE_CBD_CANNABIS",
        "INELIGIBLE_OTHER"
    ]
    
    # Explainability
    reasoning_chain: List[str]         # Step-by-step reasoning
    regulation_citations: List[RegulationCitation]
    key_factors: List[str]             # Factors that influenced decision
    
    # Metadata
    classification_timestamp: datetime
    model_version: str
    processing_time_ms: int
    data_sources_used: List[str]
    
    # Audit
    audit_id: str                      # UUID for audit trail
    request_hash: str                  # Hash of input for deduplication
```

### 4.3 Regulation Citation Schema

```python
class RegulationCitation(BaseModel):
    """Citation to specific regulation"""
    regulation_id: str                 # e.g., "7 CFR § 271.2"
    section: str                       # e.g., "eligible food definition"
    excerpt: str                       # Relevant excerpt from regulation
    relevance_score: float             # How relevant to this decision
    source_url: str                    # Link to official source
```

### 4.4 Audit Trail Schema

```python
class AuditRecord(BaseModel):
    """Complete audit record for compliance"""
    audit_id: str                      # UUID
    timestamp: datetime
    
    # Request
    request_payload: Dict[str, Any]    # Full input
    request_source: str                # API, UI, Batch
    
    # Classification
    classification_result: ClassificationResult
    
    # Processing
    model_used: str                    # e.g., "gemini-1.5-flash"
    tokens_consumed: int
    rag_documents_retrieved: List[str]
    
    # Challenge (if disputed)
    was_challenged: bool
    challenge_reason: Optional[str]
    challenge_result: Optional[ClassificationResult]
    challenge_timestamp: Optional[datetime]
```

### 4.5 SQLite Database Schema

```sql
-- Products table (cached classifications)
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT UNIQUE NOT NULL,
    product_name TEXT NOT NULL,
    upc TEXT,
    category TEXT,
    brand TEXT,
    description TEXT,
    raw_input_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Classifications table
CREATE TABLE classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT UNIQUE NOT NULL,
    product_id TEXT NOT NULL,
    is_ebt_eligible BOOLEAN NOT NULL,
    confidence_score REAL NOT NULL,
    classification_category TEXT NOT NULL,
    reasoning_chain_json TEXT NOT NULL,
    regulation_citations_json TEXT NOT NULL,
    key_factors_json TEXT NOT NULL,
    model_version TEXT NOT NULL,
    processing_time_ms INTEGER,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Audit trail table
CREATE TABLE audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT UNIQUE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    request_payload_json TEXT NOT NULL,
    request_source TEXT NOT NULL,
    classification_result_json TEXT NOT NULL,
    model_used TEXT NOT NULL,
    tokens_consumed INTEGER,
    rag_documents_json TEXT,
    was_challenged BOOLEAN DEFAULT FALSE,
    challenge_reason TEXT,
    challenge_result_json TEXT,
    challenge_timestamp TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_products_upc ON products(upc);
CREATE INDEX idx_classifications_product ON classifications(product_id);
CREATE INDEX idx_classifications_eligible ON classifications(is_ebt_eligible);
CREATE INDEX idx_audit_timestamp ON audit_trail(timestamp);
```

---

## 5. API Specification

### 5.1 Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/classify` | POST | Classify single product |
| `/bulk-classify` | POST | Classify multiple products |
| `/explain/{audit_id}` | GET | Get detailed explanation |
| `/challenge/{audit_id}` | POST | Challenge a classification |
| `/audit-trail` | GET | Query audit records |
| `/products/{product_id}` | GET | Get cached product classification |

### 5.2 Endpoint Specifications

#### POST /classify
Classify a single product for EBT eligibility.

**Request:**
```json
{
  "product_id": "SKU-12345",
  "product_name": "Monster Energy Drink Original",
  "description": "Energy drink with caffeine and B vitamins",
  "category": "Beverages",
  "brand": "Monster",
  "upc": "070847811169",
  "ingredients": ["carbonated water", "sugar", "glucose", "citric acid", "taurine", "caffeine"],
  "nutrition_label_type": "nutrition_facts",
  "is_hot_at_sale": false,
  "alcohol_content": 0.0,
  "contains_tobacco": false,
  "contains_cbd_cannabis": false
}
```

**Response:**
```json
{
  "product_id": "SKU-12345",
  "product_name": "Monster Energy Drink Original",
  "is_ebt_eligible": true,
  "confidence_score": 0.95,
  "classification_category": "ELIGIBLE_BEVERAGE",
  "reasoning_chain": [
    "Product is intended for human consumption (beverage)",
    "Product has Nutrition Facts label (not Supplement Facts)",
    "Alcohol content is 0% (below threshold)",
    "Product is not hot at point of sale",
    "Not intended for on-premises consumption",
    "Does not contain tobacco, CBD, or controlled substances",
    "CONCLUSION: Product is SNAP-eligible as a non-alcoholic beverage"
  ],
  "regulation_citations": [
    {
      "regulation_id": "7 CFR § 271.2",
      "section": "eligible food",
      "excerpt": "Any food or food product for home consumption except alcoholic beverages, tobacco, and hot food...",
      "relevance_score": 0.98,
      "source_url": "https://www.ecfr.gov/current/title-7/section-271.2"
    }
  ],
  "key_factors": [
    "Has Nutrition Facts label (not Supplement Facts)",
    "Non-alcoholic beverage",
    "Cold/room temperature product"
  ],
  "classification_timestamp": "2026-01-21T15:30:00Z",
  "model_version": "1.0.0",
  "processing_time_ms": 1250,
  "data_sources_used": ["USDA FoodData Central", "SNAP Guidelines Vector Store"],
  "audit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "request_hash": "sha256:abc123..."
}
```

#### POST /bulk-classify
Classify multiple products in a single request.

**Request:**
```json
{
  "products": [
    {"product_id": "SKU-001", "product_name": "Organic Bananas", "category": "Produce"},
    {"product_id": "SKU-002", "product_name": "Centrum Multivitamin", "category": "Health", "nutrition_label_type": "supplement_facts"},
    {"product_id": "SKU-003", "product_name": "Marlboro Cigarettes", "category": "Tobacco", "contains_tobacco": true}
  ],
  "options": {
    "parallel_processing": true,
    "max_concurrent": 5,
    "fail_fast": false
  }
}
```

**Response:**
```json
{
  "total_products": 3,
  "successful": 3,
  "failed": 0,
  "processing_time_ms": 3500,
  "results": [
    {
      "product_id": "SKU-001",
      "is_ebt_eligible": true,
      "confidence_score": 0.99,
      "classification_category": "ELIGIBLE_STAPLE_FOOD",
      "audit_id": "uuid-1"
    },
    {
      "product_id": "SKU-002",
      "is_ebt_eligible": false,
      "confidence_score": 0.99,
      "classification_category": "INELIGIBLE_SUPPLEMENT",
      "audit_id": "uuid-2"
    },
    {
      "product_id": "SKU-003",
      "is_ebt_eligible": false,
      "confidence_score": 1.0,
      "classification_category": "INELIGIBLE_TOBACCO",
      "audit_id": "uuid-3"
    }
  ],
  "summary": {
    "eligible_count": 1,
    "ineligible_count": 2,
    "low_confidence_count": 0
  }
}
```

#### POST /challenge/{audit_id}
Challenge a classification decision for re-evaluation.

**Request:**
```json
{
  "challenge_reason": "Product has been reformulated and no longer contains supplements",
  "additional_evidence": {
    "new_nutrition_label_type": "nutrition_facts",
    "updated_ingredients": ["water", "electrolytes", "natural flavors"]
  }
}
```

**Response:**
```json
{
  "original_audit_id": "uuid-original",
  "challenge_audit_id": "uuid-challenge",
  "original_classification": {
    "is_ebt_eligible": false,
    "classification_category": "INELIGIBLE_SUPPLEMENT"
  },
  "new_classification": {
    "is_ebt_eligible": true,
    "classification_category": "ELIGIBLE_BEVERAGE",
    "confidence_score": 0.92
  },
  "classification_changed": true,
  "reasoning_for_change": [
    "Original classification based on Supplement Facts label",
    "Challenge evidence shows product now has Nutrition Facts label",
    "Updated ingredients contain no supplement-grade compounds",
    "Reclassified as eligible non-alcoholic beverage"
  ]
}
```

#### GET /audit-trail
Query audit records with filters.

**Query Parameters:**
- `start_date`: ISO datetime
- `end_date`: ISO datetime
- `is_ebt_eligible`: boolean filter
- `classification_category`: category filter
- `was_challenged`: boolean filter
- `limit`: max records (default 100)
- `offset`: pagination offset

**Response:**
```json
{
  "total_records": 1250,
  "returned_records": 100,
  "records": [
    {
      "audit_id": "uuid",
      "timestamp": "2026-01-21T15:30:00Z",
      "product_id": "SKU-001",
      "product_name": "Product Name",
      "is_ebt_eligible": true,
      "classification_category": "ELIGIBLE_STAPLE_FOOD",
      "model_used": "gemini-1.5-flash",
      "was_challenged": false
    }
  ]
}
```

---

## 6. Implementation Specifications

### 6.1 Project Structure

```
ebt-classification/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Dockerfile
│
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── classify.py        # /classify, /bulk-classify
│   │   │   ├── explain.py         # /explain/{audit_id}
│   │   │   ├── challenge.py       # /challenge/{audit_id}
│   │   │   ├── audit.py           # /audit-trail
│   │   │   └── health.py          # /health
│   │   └── dependencies.py        # FastAPI dependencies
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── constants.py           # Constants and enums
│   │   └── exceptions.py          # Custom exceptions
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py             # Product input/output models
│   │   ├── classification.py      # Classification result models
│   │   ├── audit.py               # Audit trail models
│   │   └── regulation.py          # Regulation citation models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── classification_engine.py   # Main classification logic
│   │   ├── rule_validator.py          # Rule-based validation
│   │   ├── ai_reasoning_agent.py      # LangChain + Gemini agent
│   │   ├── confidence_scorer.py       # Confidence calculation
│   │   └── challenge_handler.py       # Challenge workflow
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── classification_agent.py    # LangChain agent definition
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── regulation_lookup.py   # RAG tool for regulations
│   │   │   ├── product_lookup.py      # External API lookup
│   │   │   └── decision_tree.py       # Rule-based decision tool
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── system_prompt.py       # System prompt template
│   │       └── classification_prompt.py # Classification prompt
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite connection
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── product_repo.py
│   │   │   ├── classification_repo.py
│   │   │   └── audit_repo.py
│   │   └── external/
│   │       ├── __init__.py
│   │       ├── usda_api.py        # USDA FoodData Central client
│   │       ├── openfoodfacts.py   # Open Food Facts client
│   │       └── snap_guidelines.py # SNAP regulation scraper
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── vector_store.py        # ChromaDB integration
│   │   ├── embeddings.py          # HuggingFace embeddings
│   │   ├── document_loader.py     # Load SNAP regulations
│   │   └── retriever.py           # RAG retrieval logic
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py             # structlog configuration
│       ├── hashing.py             # Request hashing
│       └── validators.py          # Input validation
│
├── data/
│   ├── regulations/               # Scraped SNAP regulation documents
│   │   ├── cfr_7_271_2.txt
│   │   ├── fns_eligible_foods.txt
│   │   └── fns_ineligible_items.txt
│   ├── chroma_db/                 # ChromaDB persistent storage
│   └── ebt_classification.db      # SQLite database
│
├── ui/
│   ├── app.py                     # Streamlit application
│   ├── pages/
│   │   ├── classify.py            # Single classification page
│   │   ├── bulk_upload.py         # Bulk classification page
│   │   ├── audit_viewer.py        # Audit trail viewer
│   │   └── challenge.py           # Challenge workflow page
│   └── components/
│       ├── product_form.py
│       ├── result_display.py
│       └── reasoning_chain.py
│
├── scripts/
│   ├── setup_database.py          # Initialize SQLite schema
│   ├── scrape_regulations.py      # Scrape SNAP guidelines
│   ├── build_vector_store.py      # Build ChromaDB index
│   └── seed_test_data.py          # Seed test products
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # pytest fixtures
│   ├── unit/
│   │   ├── test_rule_validator.py
│   │   ├── test_classification_engine.py
│   │   └── test_confidence_scorer.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_agent_reasoning.py
│   │   └── test_rag_retrieval.py
│   └── fixtures/
│       ├── products.json          # Test product data
│       └── expected_results.json  # Expected classifications
│
└── docs/
    ├── API.md                     # API documentation
    ├── ARCHITECTURE.md            # Architecture details
    └── DEPLOYMENT.md              # Deployment guide
```

### 6.2 Core Dependencies (requirements.txt)

```
# FastAPI and server
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pydantic==2.5.3
pydantic-settings==2.1.0

# LangChain and AI
langchain==0.1.0
langchain-google-genai==0.0.6
langchain-community==0.0.13

# Vector store and embeddings
chromadb==0.4.22
sentence-transformers==2.2.2

# Database
aiosqlite==0.19.0

# HTTP clients
httpx==0.26.0
aiohttp==3.9.1

# Utilities
python-dotenv==1.0.0
structlog==24.1.0
tenacity==8.2.3

# Streamlit UI
streamlit==1.30.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0

# Development
black==23.12.1
isort==5.13.2
mypy==1.8.0
```

### 6.3 Configuration (.env.example)

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Google Gemini API (free tier)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Fallback: Ollama (local)
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Database
DATABASE_URL=sqlite:///./data/ebt_classification.db

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
CHROMA_COLLECTION_NAME=snap_regulations

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# External APIs
USDA_API_KEY=your_usda_api_key_here
USDA_API_BASE_URL=https://api.nal.usda.gov/fdc/v1

# Rate Limiting
GEMINI_RPM_LIMIT=15
GEMINI_DAILY_TOKEN_LIMIT=1000000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 6.4 Key Implementation Files

#### 6.4.1 Classification Engine (src/services/classification_engine.py)

```python
"""
Main classification engine that orchestrates rule-based validation
and AI reasoning for EBT eligibility determination.
"""

import asyncio
from datetime import datetime
from typing import Optional
import uuid

from src.models.product import ProductInput
from src.models.classification import ClassificationResult, ClassificationCategory
from src.models.audit import AuditRecord
from src.services.rule_validator import RuleValidator
from src.services.ai_reasoning_agent import AIReasoningAgent
from src.services.confidence_scorer import ConfidenceScorer
from src.data.repositories.classification_repo import ClassificationRepository
from src.data.repositories.audit_repo import AuditRepository
from src.utils.hashing import compute_request_hash
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ClassificationEngine:
    """
    Orchestrates the EBT eligibility classification process.
    
    Classification Flow:
    1. Check cache for existing classification
    2. Apply rule-based validation for clear-cut cases
    3. If ambiguous, invoke AI reasoning agent
    4. Calculate confidence score
    5. Store result and audit trail
    """
    
    def __init__(
        self,
        rule_validator: RuleValidator,
        ai_agent: AIReasoningAgent,
        confidence_scorer: ConfidenceScorer,
        classification_repo: ClassificationRepository,
        audit_repo: AuditRepository,
    ):
        self.rule_validator = rule_validator
        self.ai_agent = ai_agent
        self.confidence_scorer = confidence_scorer
        self.classification_repo = classification_repo
        self.audit_repo = audit_repo
    
    async def classify(
        self,
        product: ProductInput,
        request_source: str = "API",
        force_reprocess: bool = False,
    ) -> ClassificationResult:
        """
        Classify a product for EBT eligibility.
        
        Args:
            product: Product input data
            request_source: Origin of request (API, UI, Batch)
            force_reprocess: Skip cache and reprocess
            
        Returns:
            ClassificationResult with eligibility determination
        """
        start_time = datetime.utcnow()
        audit_id = str(uuid.uuid4())
        request_hash = compute_request_hash(product)
        
        logger.info(
            "classification_started",
            product_id=product.product_id,
            audit_id=audit_id,
        )
        
        try:
            # Step 1: Check cache (unless forced reprocess)
            if not force_reprocess:
                cached = await self.classification_repo.get_by_product_id(
                    product.product_id
                )
                if cached:
                    logger.info("cache_hit", product_id=product.product_id)
                    return cached
            
            # Step 2: Apply rule-based validation
            rule_result = self.rule_validator.validate(product)
            
            if rule_result.is_deterministic:
                # Clear-cut case - use rule-based result
                logger.info(
                    "rule_based_classification",
                    product_id=product.product_id,
                    category=rule_result.category,
                )
                classification = await self._build_result(
                    product=product,
                    is_eligible=rule_result.is_eligible,
                    category=rule_result.category,
                    reasoning=rule_result.reasoning_chain,
                    citations=rule_result.citations,
                    key_factors=rule_result.key_factors,
                    confidence=1.0,  # Rule-based = high confidence
                    audit_id=audit_id,
                    request_hash=request_hash,
                    start_time=start_time,
                    data_sources=["Rule-based validator"],
                )
            else:
                # Step 3: Invoke AI reasoning agent for ambiguous cases
                logger.info(
                    "ai_reasoning_required",
                    product_id=product.product_id,
                )
                ai_result = await self.ai_agent.reason(
                    product=product,
                    partial_rule_result=rule_result,
                )
                
                # Step 4: Calculate confidence score
                confidence = self.confidence_scorer.calculate(
                    product=product,
                    rule_result=rule_result,
                    ai_result=ai_result,
                )
                
                classification = await self._build_result(
                    product=product,
                    is_eligible=ai_result.is_eligible,
                    category=ai_result.category,
                    reasoning=ai_result.reasoning_chain,
                    citations=ai_result.citations,
                    key_factors=ai_result.key_factors,
                    confidence=confidence,
                    audit_id=audit_id,
                    request_hash=request_hash,
                    start_time=start_time,
                    data_sources=ai_result.data_sources_used,
                )
            
            # Step 5: Store classification and audit trail
            await self.classification_repo.save(classification)
            await self._store_audit(
                audit_id=audit_id,
                product=product,
                result=classification,
                request_source=request_source,
            )
            
            logger.info(
                "classification_completed",
                product_id=product.product_id,
                is_eligible=classification.is_ebt_eligible,
                confidence=classification.confidence_score,
                processing_time_ms=classification.processing_time_ms,
            )
            
            return classification
            
        except Exception as e:
            logger.error(
                "classification_failed",
                product_id=product.product_id,
                error=str(e),
            )
            raise
    
    async def bulk_classify(
        self,
        products: list[ProductInput],
        max_concurrent: int = 5,
        fail_fast: bool = False,
    ) -> dict:
        """
        Classify multiple products with concurrency control.
        
        Args:
            products: List of products to classify
            max_concurrent: Max concurrent classifications
            fail_fast: Stop on first error if True
            
        Returns:
            Dict with results and summary statistics
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        errors = []
        
        async def classify_with_semaphore(product: ProductInput):
            async with semaphore:
                try:
                    result = await self.classify(product, request_source="Batch")
                    return {"success": True, "result": result}
                except Exception as e:
                    if fail_fast:
                        raise
                    return {"success": False, "product_id": product.product_id, "error": str(e)}
        
        tasks = [classify_with_semaphore(p) for p in products]
        completed = await asyncio.gather(*tasks, return_exceptions=not fail_fast)
        
        for item in completed:
            if isinstance(item, Exception):
                errors.append(str(item))
            elif item["success"]:
                results.append(item["result"])
            else:
                errors.append(item)
        
        eligible_count = sum(1 for r in results if r.is_ebt_eligible)
        low_confidence_count = sum(1 for r in results if r.confidence_score < 0.8)
        
        return {
            "total_products": len(products),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
            "summary": {
                "eligible_count": eligible_count,
                "ineligible_count": len(results) - eligible_count,
                "low_confidence_count": low_confidence_count,
            },
        }
    
    async def _build_result(
        self,
        product: ProductInput,
        is_eligible: bool,
        category: ClassificationCategory,
        reasoning: list[str],
        citations: list,
        key_factors: list[str],
        confidence: float,
        audit_id: str,
        request_hash: str,
        start_time: datetime,
        data_sources: list[str],
    ) -> ClassificationResult:
        """Build the classification result object."""
        end_time = datetime.utcnow()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return ClassificationResult(
            product_id=product.product_id,
            product_name=product.product_name,
            is_ebt_eligible=is_eligible,
            confidence_score=confidence,
            classification_category=category,
            reasoning_chain=reasoning,
            regulation_citations=citations,
            key_factors=key_factors,
            classification_timestamp=end_time,
            model_version="1.0.0",
            processing_time_ms=processing_time_ms,
            data_sources_used=data_sources,
            audit_id=audit_id,
            request_hash=request_hash,
        )
    
    async def _store_audit(
        self,
        audit_id: str,
        product: ProductInput,
        result: ClassificationResult,
        request_source: str,
    ):
        """Store audit trail record."""
        audit = AuditRecord(
            audit_id=audit_id,
            timestamp=result.classification_timestamp,
            request_payload=product.model_dump(),
            request_source=request_source,
            classification_result=result,
            model_used=self.ai_agent.model_name,
            tokens_consumed=0,  # Updated by AI agent
            rag_documents_retrieved=[],
            was_challenged=False,
        )
        await self.audit_repo.save(audit)
```

#### 6.4.2 Rule Validator (src/services/rule_validator.py)

```python
"""
Rule-based validator implementing SNAP eligibility rules from 7 CFR § 271.2.
Handles clear-cut cases without requiring AI reasoning.
"""

from dataclasses import dataclass
from typing import Optional

from src.models.product import ProductInput
from src.models.classification import ClassificationCategory
from src.models.regulation import RegulationCitation


@dataclass
class RuleValidationResult:
    """Result of rule-based validation."""
    is_deterministic: bool  # True if rules can definitively classify
    is_eligible: Optional[bool]
    category: Optional[ClassificationCategory]
    reasoning_chain: list[str]
    citations: list[RegulationCitation]
    key_factors: list[str]
    ambiguity_reason: Optional[str] = None


class RuleValidator:
    """
    Implements deterministic SNAP eligibility rules.
    
    These rules cover clear-cut cases that don't require AI reasoning:
    - Alcohol (always ineligible)
    - Tobacco (always ineligible)
    - Hot foods (always ineligible)
    - Supplements with Supplement Facts label (always ineligible)
    - Live animals except exceptions (always ineligible)
    - CBD/Cannabis products (always ineligible)
    """
    
    # Regulation citations for each rule
    CITATIONS = {
        "alcohol": RegulationCitation(
            regulation_id="7 CFR § 271.2",
            section="eligible food",
            excerpt="Eligible food means any food or food product for home consumption except alcoholic beverages",
            relevance_score=1.0,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
        "tobacco": RegulationCitation(
            regulation_id="7 CFR § 271.2",
            section="eligible food",
            excerpt="Eligible food means any food or food product for home consumption except tobacco",
            relevance_score=1.0,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
        "hot_food": RegulationCitation(
            regulation_id="7 CFR § 271.2",
            section="eligible food",
            excerpt="Hot foods or hot food products ready for immediate consumption are not eligible",
            relevance_score=1.0,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
        "supplement": RegulationCitation(
            regulation_id="FNS Policy",
            section="eligible food items",
            excerpt="Any item that has a Supplement Facts label is considered a supplement and is not eligible for SNAP purchase",
            relevance_score=1.0,
            source_url="https://www.fns.usda.gov/snap/eligible-food-items",
        ),
        "cbd_cannabis": RegulationCitation(
            regulation_id="FNS Policy",
            section="eligible food items",
            excerpt="Food containing cannabis-derived products, such as CBD, and any other controlled substances, are not eligible to be purchased with SNAP benefits",
            relevance_score=1.0,
            source_url="https://www.fns.usda.gov/snap/food-determinations-eligible-foods",
        ),
        "live_animal": RegulationCitation(
            regulation_id="FNS Policy",
            section="eligible food items",
            excerpt="Live animals (except shellfish, fish removed from water, and animals slaughtered prior to pick-up from the store) are not eligible",
            relevance_score=1.0,
            source_url="https://www.fns.usda.gov/snap/eligible-food-items",
        ),
        "eligible_food": RegulationCitation(
            regulation_id="7 CFR § 271.2",
            section="eligible food",
            excerpt="Any food or food product for home consumption",
            relevance_score=0.9,
            source_url="https://www.ecfr.gov/current/title-7/section-271.2",
        ),
    }
    
    def validate(self, product: ProductInput) -> RuleValidationResult:
        """
        Apply rule-based validation to determine eligibility.
        
        Returns deterministic result if rules apply, otherwise
        returns ambiguous result for AI processing.
        """
        reasoning = []
        key_factors = []
        
        # Rule 1: Check for alcohol
        if product.alcohol_content and product.alcohol_content > 0.005:  # >0.5% ABV
            reasoning.append(f"Product contains {product.alcohol_content * 100:.1f}% alcohol")
            reasoning.append("Alcoholic beverages are explicitly excluded from SNAP eligibility")
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_ALCOHOL,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["alcohol"]],
                key_factors=["Contains alcohol above 0.5% ABV"],
            )
        
        # Rule 2: Check for tobacco
        if product.contains_tobacco:
            reasoning.append("Product contains tobacco or nicotine")
            reasoning.append("Tobacco products are explicitly excluded from SNAP eligibility")
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_TOBACCO,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["tobacco"]],
                key_factors=["Contains tobacco/nicotine"],
            )
        
        # Rule 3: Check for hot food
        if product.is_hot_at_sale:
            reasoning.append("Product is hot at point of sale")
            reasoning.append("Hot foods ready for immediate consumption are not eligible")
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_HOT_FOOD,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["hot_food"]],
                key_factors=["Hot at point of sale"],
            )
        
        # Rule 4: Check for on-premises consumption
        if product.is_for_onsite_consumption:
            reasoning.append("Product is intended for on-premises consumption")
            reasoning.append("Foods for on-premises consumption are not eligible")
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_ONSITE_CONSUMPTION,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["hot_food"]],
                key_factors=["Intended for on-premises consumption"],
            )
        
        # Rule 5: Check for Supplement Facts label
        if product.nutrition_label_type == "supplement_facts":
            reasoning.append("Product has a Supplement Facts label (not Nutrition Facts)")
            reasoning.append("Items with Supplement Facts labels are classified as supplements, not food")
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_SUPPLEMENT,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["supplement"]],
                key_factors=["Has Supplement Facts label"],
            )
        
        # Rule 6: Check for CBD/Cannabis
        if product.contains_cbd_cannabis:
            reasoning.append("Product contains CBD, cannabis, or controlled substances")
            reasoning.append("Products with cannabis-derived ingredients are not eligible")
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_CBD_CANNABIS,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["cbd_cannabis"]],
                key_factors=["Contains CBD/cannabis"],
            )
        
        # Rule 7: Check for live animals
        if product.is_live_animal:
            reasoning.append("Product is a live animal")
            reasoning.append("Live animals are not eligible (except shellfish, fish removed from water, animals slaughtered before pickup)")
            return RuleValidationResult(
                is_deterministic=True,
                is_eligible=False,
                category=ClassificationCategory.INELIGIBLE_LIVE_ANIMAL,
                reasoning_chain=reasoning,
                citations=[self.CITATIONS["live_animal"]],
                key_factors=["Live animal"],
            )
        
        # No disqualifying rules triggered - check if we can positively classify
        # If product has Nutrition Facts label and category suggests food, likely eligible
        if product.nutrition_label_type == "nutrition_facts":
            key_factors.append("Has Nutrition Facts label")
            
            # Known food categories that are clearly eligible
            clearly_eligible_categories = [
                "produce", "fruits", "vegetables", "meat", "poultry", "fish",
                "seafood", "dairy", "bread", "bakery", "cereals", "grains",
                "pasta", "canned goods", "frozen foods", "snacks", "beverages",
                "condiments", "spices", "baby food", "infant formula"
            ]
            
            if product.category and product.category.lower() in clearly_eligible_categories:
                reasoning.append(f"Product category '{product.category}' is a standard food category")
                reasoning.append("Product has Nutrition Facts label (not Supplement Facts)")
                reasoning.append("No disqualifying factors found (alcohol, tobacco, hot, etc.)")
                reasoning.append("Product is eligible as a standard food item for home consumption")
                
                # Determine more specific category
                category = self._determine_eligible_category(product)
                
                return RuleValidationResult(
                    is_deterministic=True,
                    is_eligible=True,
                    category=category,
                    reasoning_chain=reasoning,
                    citations=[self.CITATIONS["eligible_food"]],
                    key_factors=key_factors + [f"Category: {product.category}"],
                )
        
        # Ambiguous case - needs AI reasoning
        reasoning.append("Initial rule-based validation passed (no disqualifying factors)")
        reasoning.append("Product requires AI reasoning for final classification")
        
        return RuleValidationResult(
            is_deterministic=False,
            is_eligible=None,
            category=None,
            reasoning_chain=reasoning,
            citations=[],
            key_factors=key_factors,
            ambiguity_reason="Product does not match clear-cut rules; AI reasoning required",
        )
    
    def _determine_eligible_category(self, product: ProductInput) -> ClassificationCategory:
        """Determine the specific eligible category based on product attributes."""
        category_lower = (product.category or "").lower()
        
        if any(c in category_lower for c in ["meat", "poultry", "fish", "seafood"]):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        elif any(c in category_lower for c in ["produce", "fruit", "vegetable"]):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        elif any(c in category_lower for c in ["dairy", "milk", "cheese", "yogurt"]):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        elif any(c in category_lower for c in ["bread", "bakery", "cereal", "grain", "pasta"]):
            return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
        elif any(c in category_lower for c in ["beverage", "drink", "juice", "soda"]):
            return ClassificationCategory.ELIGIBLE_BEVERAGE
        elif any(c in category_lower for c in ["snack", "chip", "candy", "cookie"]):
            return ClassificationCategory.ELIGIBLE_SNACK_FOOD
        elif any(c in category_lower for c in ["baby", "infant", "formula"]):
            return ClassificationCategory.ELIGIBLE_BABY_FOOD
        elif any(c in category_lower for c in ["spice", "condiment", "sauce", "oil"]):
            return ClassificationCategory.ELIGIBLE_COOKING_INGREDIENT
        elif any(c in category_lower for c in ["seed", "plant"]):
            return ClassificationCategory.ELIGIBLE_SEEDS_PLANTS
        else:
            return ClassificationCategory.ELIGIBLE_OTHER
```

#### 6.4.3 AI Reasoning Agent (src/agents/classification_agent.py)

```python
"""
LangChain-based AI reasoning agent for EBT eligibility classification.
Uses Gemini API with RAG for SNAP regulation lookup.
"""

from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory

from src.models.product import ProductInput
from src.models.classification import ClassificationCategory
from src.services.rule_validator import RuleValidationResult
from src.rag.retriever import SNAPRegulationRetriever
from src.core.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


SYSTEM_PROMPT = """You are an expert SNAP/EBT eligibility classification agent. Your role is to determine whether products are eligible for purchase with SNAP (Supplemental Nutrition Assistance Program) benefits based on federal regulations.

## Your Knowledge Base
You have access to:
1. SNAP eligibility regulations from 7 CFR § 271.2
2. FNS (Food and Nutrition Service) policy memoranda
3. Official USDA guidance on eligible/ineligible items

## Classification Rules (7 CFR § 271.2)

### ELIGIBLE Items (CAN be purchased with SNAP):
- Any food or food product for home consumption
- Seeds and plants that produce food for human consumption
- Non-alcoholic beverages with Nutrition Facts labels
- Snack foods, candy, ice cream (despite low nutrition value)
- Cold prepared foods not for on-premises consumption

### INELIGIBLE Items (CANNOT be purchased with SNAP):
- Alcoholic beverages (any alcohol content >0.5%)
- Tobacco products (including e-cigarettes, vapes)
- Hot foods or foods sold for immediate consumption
- Foods for on-premises consumption
- Vitamins, medicines, supplements (items with Supplement Facts label)
- Non-food items (pet food, cleaning supplies, cosmetics)
- Live animals (except shellfish, fish removed from water)
- CBD/cannabis-infused products

## Key Distinction: Nutrition Facts vs Supplement Facts
- Nutrition Facts label = FOOD (potentially eligible)
- Supplement Facts label = SUPPLEMENT (ineligible)

## Your Task
For each product, you must:
1. Analyze the product attributes
2. Search relevant SNAP regulations
3. Apply classification rules
4. Provide clear reasoning with regulation citations
5. Assign a confidence score (0.0-1.0)
6. Return structured classification

Always cite specific regulations when making decisions."""


CLASSIFICATION_PROMPT = """Classify this product for SNAP/EBT eligibility:

## Product Information
- Product ID: {product_id}
- Name: {product_name}
- Description: {description}
- Category: {category}
- Brand: {brand}
- UPC: {upc}
- Ingredients: {ingredients}
- Label Type: {nutrition_label_type}
- Hot at Sale: {is_hot_at_sale}
- For On-site Consumption: {is_for_onsite_consumption}
- Alcohol Content: {alcohol_content}
- Contains Tobacco: {contains_tobacco}
- Contains CBD/Cannabis: {contains_cbd_cannabis}
- Is Live Animal: {is_live_animal}

## Partial Rule Analysis
{partial_rule_analysis}

## Instructions
1. Use the regulation_lookup tool to find relevant SNAP guidelines
2. Analyze all product attributes against SNAP rules
3. Provide step-by-step reasoning
4. Cite specific regulations
5. Return final classification

Think step by step and be thorough in your analysis."""


class AIReasoningAgent:
    """
    AI agent for classifying ambiguous products using Gemini + RAG.
    """
    
    def __init__(
        self,
        retriever: SNAPRegulationRetriever,
        model_name: str = None,
    ):
        self.model_name = model_name or settings.GEMINI_MODEL
        self.retriever = retriever
        self._setup_agent()
    
    def _setup_agent(self):
        """Initialize the LangChain agent with tools."""
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,  # Low temperature for consistent classification
        )
        
        # Define tools
        tools = [
            Tool(
                name="regulation_lookup",
                description="Search SNAP regulations and FNS guidance for eligibility rules. Use this to find relevant regulations for product classification.",
                func=self._regulation_lookup,
            ),
            Tool(
                name="determine_eligibility",
                description="Make final eligibility determination based on gathered evidence.",
                func=self._determine_eligibility,
            ),
        ]
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_structured_chat_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt,
        )
        
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
        )
    
    def _regulation_lookup(self, query: str) -> str:
        """RAG lookup for SNAP regulations."""
        docs = self.retriever.retrieve(query, k=3)
        if not docs:
            return "No relevant regulations found."
        
        result = "Relevant SNAP Regulations:\n\n"
        for i, doc in enumerate(docs, 1):
            result += f"{i}. Source: {doc.metadata.get('source', 'Unknown')}\n"
            result += f"   Content: {doc.page_content[:500]}...\n\n"
        
        return result
    
    def _determine_eligibility(self, analysis: str) -> str:
        """Placeholder for final determination - actual logic in reason()."""
        return f"Analysis received: {analysis}"
    
    async def reason(
        self,
        product: ProductInput,
        partial_rule_result: Optional[RuleValidationResult] = None,
    ) -> "AIReasoningResult":
        """
        Use AI reasoning to classify a product.
        
        Args:
            product: Product to classify
            partial_rule_result: Partial result from rule-based validation
            
        Returns:
            AIReasoningResult with classification details
        """
        # Format input for agent
        partial_analysis = ""
        if partial_rule_result:
            partial_analysis = f"""
Previous Rule Analysis:
- Passed initial screening (no disqualifying factors found)
- Reasoning so far: {'; '.join(partial_rule_result.reasoning_chain)}
- Key factors identified: {', '.join(partial_rule_result.key_factors)}
- Ambiguity reason: {partial_rule_result.ambiguity_reason}
"""
        
        input_text = CLASSIFICATION_PROMPT.format(
            product_id=product.product_id,
            product_name=product.product_name,
            description=product.description or "Not provided",
            category=product.category or "Unknown",
            brand=product.brand or "Unknown",
            upc=product.upc or "Not provided",
            ingredients=", ".join(product.ingredients) if product.ingredients else "Not provided",
            nutrition_label_type=product.nutrition_label_type or "Unknown",
            is_hot_at_sale=product.is_hot_at_sale if product.is_hot_at_sale is not None else "Unknown",
            is_for_onsite_consumption=product.is_for_onsite_consumption if product.is_for_onsite_consumption is not None else "Unknown",
            alcohol_content=f"{product.alcohol_content * 100:.1f}%" if product.alcohol_content else "0%",
            contains_tobacco=product.contains_tobacco if product.contains_tobacco is not None else "Unknown",
            contains_cbd_cannabis=product.contains_cbd_cannabis if product.contains_cbd_cannabis is not None else "Unknown",
            is_live_animal=product.is_live_animal if product.is_live_animal is not None else "No",
            partial_rule_analysis=partial_analysis,
        )
        
        try:
            # Run agent
            result = await self.agent_executor.ainvoke({"input": input_text})
            
            # Parse agent output
            return self._parse_agent_output(result["output"], product)
            
        except Exception as e:
            logger.error("ai_reasoning_failed", error=str(e), product_id=product.product_id)
            # Fallback to conservative classification
            return AIReasoningResult(
                is_eligible=True,  # Default to eligible for food items
                category=ClassificationCategory.ELIGIBLE_OTHER,
                reasoning_chain=[
                    "AI reasoning encountered an error",
                    "Defaulting to eligible classification (conservative approach)",
                    f"Error: {str(e)}",
                ],
                citations=[],
                key_factors=["AI processing error - manual review recommended"],
                data_sources_used=["Error fallback"],
            )
    
    def _parse_agent_output(self, output: str, product: ProductInput) -> "AIReasoningResult":
        """Parse agent output into structured result."""
        # Extract eligibility determination
        output_lower = output.lower()
        
        # Determine eligibility from output
        is_eligible = True  # Default
        if any(phrase in output_lower for phrase in [
            "not eligible", "ineligible", "cannot be purchased",
            "not allowed", "prohibited", "excluded"
        ]):
            is_eligible = False
        elif any(phrase in output_lower for phrase in [
            "eligible", "can be purchased", "allowed", "permitted"
        ]):
            is_eligible = True
        
        # Determine category
        category = self._extract_category(output_lower, is_eligible)
        
        # Extract reasoning chain (split by numbered points or newlines)
        reasoning_lines = [
            line.strip() for line in output.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
        reasoning_chain = reasoning_lines[:10]  # Limit to 10 steps
        
        # Extract key factors
        key_factors = []
        if "supplement facts" in output_lower:
            key_factors.append("Supplement Facts label identified")
        if "nutrition facts" in output_lower:
            key_factors.append("Nutrition Facts label identified")
        if product.category:
            key_factors.append(f"Product category: {product.category}")
        
        return AIReasoningResult(
            is_eligible=is_eligible,
            category=category,
            reasoning_chain=reasoning_chain,
            citations=[],  # Would be extracted from RAG results
            key_factors=key_factors or ["AI analysis completed"],
            data_sources_used=["Gemini AI", "SNAP Regulation Vector Store"],
        )
    
    def _extract_category(self, output: str, is_eligible: bool) -> ClassificationCategory:
        """Extract classification category from agent output."""
        if not is_eligible:
            if "alcohol" in output:
                return ClassificationCategory.INELIGIBLE_ALCOHOL
            elif "tobacco" in output:
                return ClassificationCategory.INELIGIBLE_TOBACCO
            elif "hot" in output:
                return ClassificationCategory.INELIGIBLE_HOT_FOOD
            elif "supplement" in output:
                return ClassificationCategory.INELIGIBLE_SUPPLEMENT
            elif "medicine" in output or "vitamin" in output:
                return ClassificationCategory.INELIGIBLE_MEDICINE
            elif "cbd" in output or "cannabis" in output:
                return ClassificationCategory.INELIGIBLE_CBD_CANNABIS
            elif "live animal" in output:
                return ClassificationCategory.INELIGIBLE_LIVE_ANIMAL
            elif "non-food" in output or "non food" in output:
                return ClassificationCategory.INELIGIBLE_NON_FOOD
            else:
                return ClassificationCategory.INELIGIBLE_OTHER
        else:
            if "staple" in output:
                return ClassificationCategory.ELIGIBLE_STAPLE_FOOD
            elif "snack" in output:
                return ClassificationCategory.ELIGIBLE_SNACK_FOOD
            elif "beverage" in output or "drink" in output:
                return ClassificationCategory.ELIGIBLE_BEVERAGE
            elif "baby" in output or "infant" in output:
                return ClassificationCategory.ELIGIBLE_BABY_FOOD
            elif "seed" in output or "plant" in output:
                return ClassificationCategory.ELIGIBLE_SEEDS_PLANTS
            elif "cooking" in output or "ingredient" in output:
                return ClassificationCategory.ELIGIBLE_COOKING_INGREDIENT
            else:
                return ClassificationCategory.ELIGIBLE_OTHER


@dataclass
class AIReasoningResult:
    """Result from AI reasoning agent."""
    is_eligible: bool
    category: ClassificationCategory
    reasoning_chain: list[str]
    citations: list
    key_factors: list[str]
    data_sources_used: list[str]
```

### 6.5 Streamlit UI Specification

#### 6.5.1 Main App Layout (ui/app.py)

```python
"""
Streamlit UI for EBT Eligibility Classification Demo.
"""

import streamlit as st

st.set_page_config(
    page_title="EBT Eligibility Classifier",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation
st.sidebar.title("EBT Eligibility Classifier")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Single Classification", "Bulk Upload", "Audit Trail", "Challenge Decision"],
)

if page == "Single Classification":
    from ui.pages.classify import render_classify_page
    render_classify_page()
elif page == "Bulk Upload":
    from ui.pages.bulk_upload import render_bulk_page
    render_bulk_page()
elif page == "Audit Trail":
    from ui.pages.audit_viewer import render_audit_page
    render_audit_page()
elif page == "Challenge Decision":
    from ui.pages.challenge import render_challenge_page
    render_challenge_page()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Regulations:** 7 CFR § 271.2  
**Data Sources:** USDA, Open Food Facts  
**Stack:** 100% Free Tier
""")
```

#### 6.5.2 UI Components

The UI should include these key components:

**Single Classification Page:**
- Product input form with all fields
- Real-time validation
- Submit button with loading state
- Result display with:
  - Large eligibility badge (ELIGIBLE/INELIGIBLE)
  - Confidence score gauge
  - Classification category
  - Expandable reasoning chain
  - Regulation citations with links
  - Key factors list

**Bulk Upload Page:**
- CSV file upload
- Column mapping interface
- Progress bar during processing
- Results table with export option
- Summary statistics

**Audit Trail Page:**
- Date range filter
- Eligibility filter
- Category filter
- Paginated results table
- Export to CSV

**Challenge Page:**
- Audit ID lookup
- Original classification display
- Challenge reason input
- Additional evidence form
- Side-by-side comparison of original vs new

---

## 7. Test Cases

### 7.1 Unit Test Cases

```python
# tests/unit/test_rule_validator.py

import pytest
from src.services.rule_validator import RuleValidator
from src.models.product import ProductInput


class TestRuleValidator:
    """Test cases for rule-based validation."""
    
    @pytest.fixture
    def validator(self):
        return RuleValidator()
    
    # INELIGIBLE CASES
    
    def test_alcohol_ineligible(self, validator):
        """Alcoholic beverages should be ineligible."""
        product = ProductInput(
            product_id="BEER-001",
            product_name="Budweiser Beer",
            category="Beverages",
            alcohol_content=0.05,  # 5% ABV
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == "INELIGIBLE_ALCOHOL"
    
    def test_tobacco_ineligible(self, validator):
        """Tobacco products should be ineligible."""
        product = ProductInput(
            product_id="CIG-001",
            product_name="Marlboro Red",
            category="Tobacco",
            contains_tobacco=True,
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == "INELIGIBLE_TOBACCO"
    
    def test_hot_food_ineligible(self, validator):
        """Hot foods should be ineligible."""
        product = ProductInput(
            product_id="HOT-001",
            product_name="Rotisserie Chicken",
            category="Prepared Foods",
            is_hot_at_sale=True,
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == "INELIGIBLE_HOT_FOOD"
    
    def test_supplement_ineligible(self, validator):
        """Products with Supplement Facts label should be ineligible."""
        product = ProductInput(
            product_id="VIT-001",
            product_name="Centrum Multivitamin",
            category="Health",
            nutrition_label_type="supplement_facts",
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == "INELIGIBLE_SUPPLEMENT"
    
    def test_cbd_ineligible(self, validator):
        """CBD products should be ineligible."""
        product = ProductInput(
            product_id="CBD-001",
            product_name="CBD Gummies",
            category="Health",
            contains_cbd_cannabis=True,
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == "INELIGIBLE_CBD_CANNABIS"
    
    def test_live_animal_ineligible(self, validator):
        """Live animals should be ineligible."""
        product = ProductInput(
            product_id="ANIMAL-001",
            product_name="Live Chicken",
            category="Poultry",
            is_live_animal=True,
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is False
        assert result.category == "INELIGIBLE_LIVE_ANIMAL"
    
    # ELIGIBLE CASES
    
    def test_produce_eligible(self, validator):
        """Fresh produce should be eligible."""
        product = ProductInput(
            product_id="PROD-001",
            product_name="Organic Bananas",
            category="Produce",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == "ELIGIBLE_STAPLE_FOOD"
    
    def test_beverage_with_nutrition_facts_eligible(self, validator):
        """Non-alcoholic beverages with Nutrition Facts should be eligible."""
        product = ProductInput(
            product_id="BEV-001",
            product_name="Monster Energy Drink",
            category="Beverages",
            nutrition_label_type="nutrition_facts",
            alcohol_content=0.0,
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == "ELIGIBLE_BEVERAGE"
    
    def test_snack_eligible(self, validator):
        """Snack foods should be eligible."""
        product = ProductInput(
            product_id="SNACK-001",
            product_name="Lay's Potato Chips",
            category="Snacks",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == "ELIGIBLE_SNACK_FOOD"
    
    def test_baby_food_eligible(self, validator):
        """Baby food should be eligible."""
        product = ProductInput(
            product_id="BABY-001",
            product_name="Gerber Baby Cereal",
            category="Baby Food",
            nutrition_label_type="nutrition_facts",
        )
        result = validator.validate(product)
        assert result.is_deterministic is True
        assert result.is_eligible is True
        assert result.category == "ELIGIBLE_BABY_FOOD"
    
    # AMBIGUOUS CASES
    
    def test_unknown_product_ambiguous(self, validator):
        """Products without clear category need AI reasoning."""
        product = ProductInput(
            product_id="UNK-001",
            product_name="Mystery Item",
            description="An item of unknown type",
        )
        result = validator.validate(product)
        assert result.is_deterministic is False
        assert result.ambiguity_reason is not None
```

### 7.2 Integration Test Cases

```python
# tests/integration/test_api_endpoints.py

import pytest
from httpx import AsyncClient
from src.main import app


@pytest.mark.asyncio
class TestClassifyEndpoint:
    """Integration tests for /classify endpoint."""
    
    async def test_classify_eligible_product(self, async_client: AsyncClient):
        """Test classification of eligible product."""
        response = await async_client.post("/classify", json={
            "product_id": "TEST-001",
            "product_name": "Fresh Apples",
            "category": "Produce",
            "nutrition_label_type": "nutrition_facts",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is True
        assert data["confidence_score"] >= 0.9
        assert "audit_id" in data
    
    async def test_classify_ineligible_alcohol(self, async_client: AsyncClient):
        """Test classification of alcoholic product."""
        response = await async_client.post("/classify", json={
            "product_id": "TEST-002",
            "product_name": "Red Wine",
            "category": "Beverages",
            "alcohol_content": 0.13,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["is_ebt_eligible"] is False
        assert data["classification_category"] == "INELIGIBLE_ALCOHOL"
    
    async def test_bulk_classify(self, async_client: AsyncClient):
        """Test bulk classification endpoint."""
        response = await async_client.post("/bulk-classify", json={
            "products": [
                {"product_id": "B1", "product_name": "Bananas", "category": "Produce"},
                {"product_id": "B2", "product_name": "Beer", "alcohol_content": 0.05},
            ],
            "options": {"parallel_processing": True}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 2
        assert data["successful"] == 2
        assert data["summary"]["eligible_count"] == 1
        assert data["summary"]["ineligible_count"] == 1
```

### 7.3 Test Product Dataset

```json
// tests/fixtures/products.json
{
  "eligible_products": [
    {
      "product_id": "E001",
      "product_name": "Organic Whole Milk",
      "category": "Dairy",
      "expected_category": "ELIGIBLE_STAPLE_FOOD"
    },
    {
      "product_id": "E002",
      "product_name": "Cheerios Cereal",
      "category": "Cereals",
      "expected_category": "ELIGIBLE_STAPLE_FOOD"
    },
    {
      "product_id": "E003",
      "product_name": "Coca-Cola Classic",
      "category": "Beverages",
      "nutrition_label_type": "nutrition_facts",
      "expected_category": "ELIGIBLE_BEVERAGE"
    },
    {
      "product_id": "E004",
      "product_name": "Snickers Bar",
      "category": "Snacks",
      "expected_category": "ELIGIBLE_SNACK_FOOD"
    },
    {
      "product_id": "E005",
      "product_name": "Vegetable Seeds Assortment",
      "category": "Seeds",
      "expected_category": "ELIGIBLE_SEEDS_PLANTS"
    }
  ],
  "ineligible_products": [
    {
      "product_id": "I001",
      "product_name": "Budweiser 6-Pack",
      "category": "Beverages",
      "alcohol_content": 0.05,
      "expected_category": "INELIGIBLE_ALCOHOL"
    },
    {
      "product_id": "I002",
      "product_name": "Marlboro Cigarettes",
      "category": "Tobacco",
      "contains_tobacco": true,
      "expected_category": "INELIGIBLE_TOBACCO"
    },
    {
      "product_id": "I003",
      "product_name": "Hot Pizza Slice",
      "category": "Prepared Foods",
      "is_hot_at_sale": true,
      "expected_category": "INELIGIBLE_HOT_FOOD"
    },
    {
      "product_id": "I004",
      "product_name": "One A Day Multivitamin",
      "category": "Health",
      "nutrition_label_type": "supplement_facts",
      "expected_category": "INELIGIBLE_SUPPLEMENT"
    },
    {
      "product_id": "I005",
      "product_name": "Dog Food - Kibble",
      "category": "Pet Supplies",
      "expected_category": "INELIGIBLE_NON_FOOD"
    }
  ]
}
```

---

## 8. Deployment Specification

### 8.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY data/regulations/ ./data/regulations/
COPY scripts/ ./scripts/

# Initialize database and vector store
RUN python scripts/setup_database.py
RUN python scripts/build_vector_store.py

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - USDA_API_KEY=${USDA_API_KEY}
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ui:
    build:
      context: .
      dockerfile: Dockerfile.ui
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
```

### 8.3 Render.com Deployment (render.yaml)

```yaml
services:
  - type: web
    name: ebt-classifier-api
    env: python
    buildCommand: pip install -r requirements.txt && python scripts/setup_database.py && python scripts/build_vector_store.py
    startCommand: uvicorn src.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
      - key: USDA_API_KEY
        sync: false
    healthCheckPath: /health
    plan: free
```

---

## 9. Success Metrics

### 9.1 Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Classification Accuracy | >95% | Manual validation against known products |
| Clear-cut Case Accuracy | 100% | Alcohol, tobacco, supplements correctly identified |
| API Response Time (single) | <3 seconds | P95 latency |
| API Response Time (bulk 100) | <60 seconds | Total processing time |
| System Availability | 99% | Uptime during demo |

### 9.2 Demo Checklist

- [ ] Single product classification works
- [ ] Bulk upload (CSV) works
- [ ] Explainability shows reasoning chain
- [ ] Regulation citations display correctly
- [ ] Audit trail is queryable
- [ ] Challenge workflow re-evaluates
- [ ] UI is responsive and clear
- [ ] All test cases pass

---

## 10. Appendix

### 10.1 Glossary

| Term | Definition |
|------|------------|
| **SNAP** | Supplemental Nutrition Assistance Program (formerly Food Stamps) |
| **EBT** | Electronic Benefits Transfer - card used to distribute SNAP benefits |
| **CFR** | Code of Federal Regulations |
| **FNS** | Food and Nutrition Service (USDA division) |
| **RAG** | Retrieval Augmented Generation |
| **Staple Food** | Basic food items in meat/poultry/fish, bread/cereals, vegetables/fruits, dairy |
| **Accessory Food** | Snacks, desserts, condiments - complement meals |

### 10.2 Reference Links

- [7 CFR § 271.2 - SNAP Definitions](https://www.ecfr.gov/current/title-7/section-271.2)
- [FNS Eligible Food Items](https://www.fns.usda.gov/snap/eligible-food-items)
- [USDA FoodData Central API](https://fdc.nal.usda.gov/api-guide.html)
- [Open Food Facts API](https://wiki.openfoodfacts.org/API)
- [Google Gemini API](https://ai.google.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

---

**Document Version:** 1.0  
**Last Updated:** January 21, 2026  
**Author:** Lokesh Mure (AI-Assisted)
