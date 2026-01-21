# EBT Eligibility Classification API Documentation

## Base URL

- Development: `http://localhost:8000`
- Production: `https://your-deployment-url.com`

## Authentication

Currently, the API does not require authentication. In production, consider adding:
- API key authentication
- OAuth 2.0
- JWT tokens

## Endpoints

### Health Check

#### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-21T15:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "vector_store": "healthy",
    "ai_service": "available"
  }
}
```

---

### Classification

#### POST /classify

Classify a single product for EBT eligibility.

**Request Body:**
```json
{
  "product_id": "SKU-12345",
  "product_name": "Monster Energy Drink",
  "category": "Beverages",
  "brand": "Monster",
  "upc": "070847811169",
  "description": "16oz energy drink with caffeine and B-vitamins",
  "nutrition_label_type": "nutrition_facts",
  "is_hot_at_sale": false,
  "alcohol_content": 0.0,
  "contains_tobacco": false,
  "contains_cbd_cannabis": false,
  "is_live_animal": false,
  "is_for_onsite_consumption": false,
  "ingredients": ["carbonated water", "sugar", "caffeine", "taurine"]
}
```

**Required Fields:**
- `product_id`: Unique identifier for the product
- `product_name`: Name of the product

**Optional Fields:**
- `category`: Product category (helps with classification)
- `brand`: Brand name
- `upc`: Universal Product Code
- `description`: Product description
- `nutrition_label_type`: "nutrition_facts", "supplement_facts", or "none"
- `is_hot_at_sale`: Whether product is sold hot
- `alcohol_content`: Alcohol content as decimal (0.05 = 5%)
- `contains_tobacco`: Whether product contains tobacco
- `contains_cbd_cannabis`: Whether product contains CBD/cannabis
- `is_live_animal`: Whether product is a live animal
- `is_for_onsite_consumption`: Whether product is for eating on premises
- `ingredients`: List of ingredients

**Response:**
```json
{
  "product_id": "SKU-12345",
  "product_name": "Monster Energy Drink",
  "is_ebt_eligible": true,
  "confidence_score": 0.95,
  "classification_category": "ELIGIBLE_BEVERAGE",
  "reasoning_chain": [
    "Product is a beverage (energy drink)",
    "Product has Nutrition Facts label",
    "Alcohol content is 0% (below 0.5% threshold)",
    "Product is not hot at point of sale",
    "No other disqualifying factors found",
    "CONCLUSION: Product is SNAP-eligible as a non-alcoholic beverage"
  ],
  "regulation_citations": [
    {
      "regulation_id": "7 CFR 271.2",
      "section": "eligible food",
      "excerpt": "Any food or food product for home consumption except alcoholic beverages",
      "relevance_score": 0.98,
      "source_url": "https://www.ecfr.gov/current/title-7/section-271.2"
    }
  ],
  "key_factors": [
    "Has Nutrition Facts label",
    "Non-alcoholic beverage",
    "For home consumption"
  ],
  "classification_timestamp": "2026-01-21T15:30:00Z",
  "model_version": "1.0.0",
  "processing_time_ms": 125,
  "data_sources_used": ["Rule-based validator"],
  "audit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "request_hash": "sha256:abc123..."
}
```

---

#### POST /classify/bulk

Classify multiple products in a single request.

**Request Body:**
```json
{
  "products": [
    {
      "product_id": "SKU-001",
      "product_name": "Fresh Apples",
      "category": "Produce"
    },
    {
      "product_id": "SKU-002",
      "product_name": "Budweiser Beer",
      "category": "Beverages",
      "alcohol_content": 0.05
    }
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
  "total_products": 2,
  "successful": 2,
  "failed": 0,
  "processing_time_ms": 250,
  "results": [
    {
      "product_id": "SKU-001",
      "product_name": "Fresh Apples",
      "is_ebt_eligible": true,
      "confidence_score": 0.95,
      "classification_category": "ELIGIBLE_STAPLE_FOOD",
      "audit_id": "..."
    },
    {
      "product_id": "SKU-002",
      "product_name": "Budweiser Beer",
      "is_ebt_eligible": false,
      "confidence_score": 0.99,
      "classification_category": "INELIGIBLE_ALCOHOL",
      "audit_id": "..."
    }
  ],
  "errors": [],
  "summary": {
    "eligible_count": 1,
    "ineligible_count": 1,
    "low_confidence_count": 0
  }
}
```

---

### Explanation

#### GET /explain/{audit_id}

Get detailed explanation for a classification.

**Path Parameters:**
- `audit_id`: UUID of the classification audit record

**Response:**
```json
{
  "product": {
    "product_id": "SKU-12345",
    "product_name": "Monster Energy Drink",
    "category": "Beverages"
  },
  "classification": {
    "is_ebt_eligible": true,
    "confidence_score": 0.95,
    "classification_category": "ELIGIBLE_BEVERAGE"
  },
  "explanation": {
    "reasoning_chain": [
      "Product is a beverage (energy drink)",
      "Product has Nutrition Facts label",
      "Alcohol content is 0%"
    ],
    "key_factors": [
      "Has Nutrition Facts label",
      "Non-alcoholic"
    ],
    "data_sources": ["Rule-based validator"]
  },
  "regulations": [
    {
      "regulation_id": "7 CFR 271.2",
      "section": "eligible food",
      "excerpt": "Any food or food product for home consumption..."
    }
  ],
  "metadata": {
    "classification_timestamp": "2026-01-21T15:30:00Z",
    "model_version": "1.0.0",
    "processing_time_ms": 125
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Classification not found"
}
```

---

### Challenge

#### POST /challenge/{audit_id}

Challenge a classification decision.

**Path Parameters:**
- `audit_id`: UUID of the classification to challenge

**Request Body:**
```json
{
  "challenge_reason": "This product is actually non-alcoholic. The alcohol content was incorrectly recorded.",
  "additional_evidence": {
    "alcohol_content": 0.0,
    "new_description": "Non-alcoholic beer alternative",
    "new_nutrition_label_type": "nutrition_facts"
  }
}
```

**Response:**
```json
{
  "challenge_id": "ch-12345",
  "original_classification": {
    "is_ebt_eligible": false,
    "classification_category": "INELIGIBLE_ALCOHOL",
    "confidence_score": 0.99
  },
  "new_classification": {
    "is_ebt_eligible": true,
    "classification_category": "ELIGIBLE_BEVERAGE",
    "confidence_score": 0.95
  },
  "classification_changed": true,
  "reasoning_for_change": [
    "Updated alcohol content shows 0% (below threshold)",
    "Product now qualifies as non-alcoholic beverage",
    "Reclassified as ELIGIBLE_BEVERAGE"
  ],
  "challenge_timestamp": "2026-01-21T16:00:00Z"
}
```

---

### Audit Trail

#### GET /audit-trail

List classification history with filtering.

**Query Parameters:**
- `limit`: Maximum records to return (default: 100, max: 1000)
- `offset`: Number of records to skip (for pagination)
- `is_ebt_eligible`: Filter by eligibility (true/false)
- `was_challenged`: Filter by challenge status (true/false)
- `product_id`: Filter by specific product ID
- `start_date`: Filter by date range start (ISO 8601)
- `end_date`: Filter by date range end (ISO 8601)

**Response:**
```json
{
  "records": [
    {
      "audit_id": "a1b2c3d4...",
      "timestamp": "2026-01-21T15:30:00Z",
      "product_id": "SKU-12345",
      "product_name": "Monster Energy Drink",
      "is_ebt_eligible": true,
      "classification_category": "ELIGIBLE_BEVERAGE",
      "confidence_score": 0.95,
      "was_challenged": false
    }
  ],
  "total_records": 150,
  "returned_records": 100,
  "offset": 0
}
```

---

#### GET /audit-trail/stats

Get classification statistics.

**Response:**
```json
{
  "total_classifications": 1500,
  "eligible_count": 1200,
  "ineligible_count": 300,
  "challenged_count": 25,
  "average_confidence": 0.92,
  "classifications_by_category": {
    "ELIGIBLE_STAPLE_FOOD": 800,
    "ELIGIBLE_BEVERAGE": 300,
    "INELIGIBLE_ALCOHOL": 150,
    "INELIGIBLE_SUPPLEMENT": 100
  }
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request body"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "product_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Classification failed: Internal error"
}
```

---

## Rate Limiting

The API does not currently implement rate limiting. For production deployments, consider adding:
- Request rate limits per IP/API key
- Burst limits for bulk endpoints
- Queue-based processing for large batches

---

## Versioning

The API version is included in response headers:
```
X-API-Version: 1.0.0
```

Future versions will be accessible via URL path:
- `/v1/classify`
- `/v2/classify`
