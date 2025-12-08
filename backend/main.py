"""
FlightChain Backend - Main Entry Point

This module provides the FastAPI application with all routes,
middleware, and startup configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from routers import flights, blockchain


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize database (with error handling)
    # Import models first so SQLAlchemy registers them
    import models  # This ensures all models are registered with Base.metadata
    from database import init_db
    try:
        print("Initializing database...")
        init_db()
        print(f"Database: {settings.database_url.split('@')[-1]}")
    except Exception as e:
        print(f"⚠️  Warning: Database initialization failed: {e}")
        print("⚠️  The API will still start, but database operations may fail.")
        print("⚠️  Please ensure MySQL is running and accessible.")
    
    print(f"Blockchain: {settings.ganache_url}")
    yield
    # Shutdown
    print("Shutting down FlightChain API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## FlightChain API
    
    Blockchain-backed flight tracking API that provides:
    
    - **Flight Search**: Search for flights by flight number
    - **Event Timeline**: View flight events with blockchain verification
    - **Delay Analysis**: Automated delay reason derivation
    - **Blockchain Verification**: Verify event integrity on-chain
    - **Historical Data**: View route performance baselines
    
    All flight events are hashed and recorded on-chain for immutable verification.
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS - MUST be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add exception handler to ensure CORS headers on errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Ensure CORS headers are present even on exceptions."""
    from fastapi.responses import JSONResponse
    from fastapi import status
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": settings.cors_origins[0] if settings.cors_origins else "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Include routers
app.include_router(flights.router, prefix="/api", tags=["Flights"])
app.include_router(blockchain.router, prefix="/api", tags=["Blockchain"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint returning API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }
