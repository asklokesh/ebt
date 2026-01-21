"""Classification endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_engine
from src.core.exceptions import ClassificationError, ValidationError
from src.models.classification import BulkClassificationResult, ClassificationResult
from src.models.product import BulkClassifyRequest, ProductInput
from src.services.classification_engine import ClassificationEngine

router = APIRouter(prefix="/classify", tags=["classification"])


@router.post("", response_model=ClassificationResult)
@router.post("/", response_model=ClassificationResult)
async def classify_product(
    product: ProductInput,
    force_reprocess: bool = False,
    engine: ClassificationEngine = Depends(get_engine),
) -> ClassificationResult:
    """
    Classify a single product for EBT eligibility.

    Args:
        product: Product input data
        force_reprocess: Skip cache and reprocess

    Returns:
        ClassificationResult with eligibility determination
    """
    try:
        result = await engine.classify(
            product=product,
            request_source="API",
            force_reprocess=force_reprocess,
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClassificationError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=BulkClassificationResult)
async def bulk_classify(
    request: BulkClassifyRequest,
    engine: ClassificationEngine = Depends(get_engine),
) -> BulkClassificationResult:
    """
    Classify multiple products in a single request.

    Args:
        request: Bulk classification request with products and options

    Returns:
        BulkClassificationResult with results and summary
    """
    try:
        options = request.options or {}

        result = await engine.bulk_classify(
            products=request.products,
            max_concurrent=getattr(options, "max_concurrent", 5),
            fail_fast=getattr(options, "fail_fast", False),
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
