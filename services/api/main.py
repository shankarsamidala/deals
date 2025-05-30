"""
FastAPI application for Telegram Deal Monitor API service.
Provides health checks and database connectivity endpoints.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

# Add project root to Python path and change working directory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Change working directory to project root so .env can be found
import os
os.chdir(project_root)

from core.config.settings import settings
from core.database.connection import db_connection

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown"""

    # Startup
    logger.info("Starting API service", port=settings.api_service_port)

    # Connect to database
    connected = await db_connection.connect()
    if not connected:
        logger.error("Failed to connect to database on startup")
    else:
        logger.info("Database connected successfully on startup")

    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down API service")
        await db_connection.disconnect()
        logger.info("Database disconnected on shutdown")


# Create FastAPI app
app = FastAPI(
    title="Telegram Deal Monitor API",
    description="API service for monitoring Telegram deal channels",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with basic service info"""
    return {
        "service": "Telegram Deal Monitor API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "api",
        "environment": settings.environment,
        "database_connected": db_connection.is_connected
    }


# Database health endpoint
@app.get("/health/database")
async def database_health():
    """Detailed database health check"""
    health_info = await db_connection.health_check()
    return {
        "service": "database",
        **health_info
    }


# Database collections endpoint
@app.get("/database/collections")
async def get_collections():
    """Get database collections information"""
    collections_info = await db_connection.get_collections_info()
    return {
        "database": settings.mongodb_database,
        **collections_info
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_service_host,
        port=settings.api_service_port,
        log_level=settings.log_level.lower()
    )