# EBT Eligibility Classification System

An AI-powered classification engine that determines whether retail products are eligible for SNAP/EBT purchase based on USDA regulations (7 CFR 271.2).

**Live Demo:** https://htcinc-classify-ebt.streamlit.app/

## Features

- **Rule-Based Classification**: Deterministic validation for clear-cut cases (alcohol, tobacco, supplements, hot food, etc.)
- **AI-Powered Reasoning**: LangChain + Google Gemini for ambiguous product classification
- **RAG System**: ChromaDB vector store with SNAP regulations for context-aware decisions
- **Explainable Results**: Full reasoning chain and regulation citations for every classification
- **Challenge Workflow**: Users can dispute classifications with additional evidence
- **Audit Trail**: Complete history of all classifications with filtering and search
- **Bulk Processing**: Classify multiple products concurrently

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **AI/ML**: LangChain, Google Gemini, HuggingFace sentence-transformers
- **Vector Store**: ChromaDB
- **Database**: SQLite with aiosqlite
- **Frontend**: Streamlit
- **Logging**: structlog (JSON format)

## SNAP Eligibility Rules (7 CFR 271.2)

**Eligible Items:**
- Food products for home consumption
- Seeds and plants that produce food
- Non-alcoholic beverages
- Snack foods with Nutrition Facts labels

**Ineligible Items:**
- Alcoholic beverages (>0.5% ABV)
- Tobacco products
- Vitamins/supplements (Supplement Facts label)
- Hot foods ready for immediate consumption
- Food prepared for on-premises consumption
- Live animals (with exceptions)
- CBD/cannabis products

## Quick Start

### Prerequisites

- Python 3.11+
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/asklokesh/ebt.git
cd ebt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

```bash
# Required for AI reasoning (optional - falls back to rule-based only)
GOOGLE_API_KEY=your_google_api_key

# Optional - for enhanced product data
USDA_API_KEY=your_usda_api_key
```

### Running the API

```bash
# Development mode
uvicorn src.main:app --reload --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Running the UI

```bash
streamlit run ui/app.py
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=src --cov-report=html
```

## API Endpoints

### Classification

**POST /classify**
```json
{
  "product_id": "SKU-12345",
  "product_name": "Monster Energy Drink",
  "category": "Beverages",
  "nutrition_label_type": "nutrition_facts",
  "alcohol_content": 0.0
}
```

**POST /classify/bulk**
```json
{
  "products": [...],
  "options": {
    "parallel_processing": true,
    "max_concurrent": 5
  }
}
```

### Explanation

**GET /explain/{audit_id}**

Returns detailed explanation including:
- Classification result
- Reasoning chain
- Regulation citations
- Key factors

### Challenge

**POST /challenge/{audit_id}**
```json
{
  "challenge_reason": "Product is actually non-alcoholic",
  "additional_evidence": {
    "alcohol_content": 0.0
  }
}
```

### Audit Trail

**GET /audit-trail**

Query parameters:
- `limit`: Max records to return
- `is_ebt_eligible`: Filter by eligibility
- `was_challenged`: Filter by challenge status
- `product_id`: Filter by product

**GET /audit-trail/stats**

Returns classification statistics.

## Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# Access API at http://localhost:8000
# Access UI at http://localhost:8501
```

## Render Deployment

1. Fork this repository
2. Create a new Blueprint on Render
3. Connect your forked repository
4. Set environment variables (GOOGLE_API_KEY, USDA_API_KEY)
5. Deploy

## Project Structure

```
ebt/
├── src/
│   ├── api/routes/          # FastAPI endpoints
│   ├── agents/              # AI reasoning agent
│   ├── core/                # Config, constants, exceptions
│   ├── data/                # Database, repositories
│   ├── models/              # Pydantic models
│   ├── rag/                 # RAG system components
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── ui/
│   ├── pages/               # Streamlit pages
│   └── components/          # UI components
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test data
├── data/
│   └── regulations/         # SNAP regulation documents
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.ui
├── render.yaml
└── requirements.txt
```

## Classification Categories

**Eligible:**
- `ELIGIBLE_STAPLE_FOOD` - Basic food items (meat, dairy, produce, etc.)
- `ELIGIBLE_BEVERAGE` - Non-alcoholic drinks
- `ELIGIBLE_SNACK_FOOD` - Snacks with Nutrition Facts
- `ELIGIBLE_BABY_FOOD` - Infant food products
- `ELIGIBLE_SEEDS_PLANTS` - Seeds/plants for food production
- `ELIGIBLE_COOKING_INGREDIENT` - Spices, oils, condiments
- `ELIGIBLE_OTHER` - Other eligible foods

**Ineligible:**
- `INELIGIBLE_ALCOHOL` - Alcoholic beverages
- `INELIGIBLE_TOBACCO` - Tobacco/nicotine products
- `INELIGIBLE_HOT_FOOD` - Hot prepared food
- `INELIGIBLE_SUPPLEMENT` - Dietary supplements
- `INELIGIBLE_CBD_CANNABIS` - Cannabis products
- `INELIGIBLE_LIVE_ANIMAL` - Live animals
- `INELIGIBLE_ONSITE_CONSUMPTION` - Restaurant meals
- `INELIGIBLE_OTHER` - Other ineligible items

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
