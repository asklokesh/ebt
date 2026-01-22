"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import shutdown_event, startup_event
from src.api.routes import audit, challenge, classify, explain, health, search
from src.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()


# Create FastAPI application
app = FastAPI(
    title="EBT Eligibility Classification API",
    description="""
AI-powered SNAP/EBT eligibility classification system.

This API provides:
- Product classification for EBT eligibility
- Bulk classification support
- Detailed explanations with regulation citations
- Challenge workflow for disputing classifications
- Complete audit trail

Based on USDA SNAP regulations (7 CFR 271.2).
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(classify.router)
app.include_router(explain.router)
app.include_router(challenge.router)
app.include_router(audit.router)
app.include_router(search.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
