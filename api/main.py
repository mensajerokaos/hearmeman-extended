"""
Media Analysis API - Main Application

FastAPI application with repository pattern integration.
Provides REST endpoints for media analysis job management.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.database import (
    create_async_engine_configured,
    get_engine,
    close_engine,
    get_sessionmaker,
    init_session_factory,
    verify_database_connection,
)
from api.models.base import Base
from api.models.job import AnalysisJob
from api.models.media import MediaFile
from api.models.result import AnalysisResult
from api.models.transcription import Transcription
from api.models.dependencies import get_db, JobRepositoryDependency
from api.repositories.job import JobRepository
from api.schemas.job import JobCreate, JobResponse, JobListResponse, JobUpdate


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Initializes database connection and verifies connectivity.
    """
    # Startup
    logger.info("Starting Media Analysis API...")

    try:
        # Initialize database engine
        engine = create_async_engine_configured()
        set_engine = init_session_factory(engine)

        # Verify database connection
        connected = await verify_database_connection()
        if connected:
            logger.info("Database connection established successfully")
        else:
            logger.warning("Database connection verification failed")

        # Create tables (for development - use migrations in production)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Application startup complete")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Media Analysis API...")
    await close_engine()
    logger.info("Application shutdown complete")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Media Analysis API",
    description="REST API for media analysis job management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# =============================================================================
# Middleware
# =============================================================================

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """
    Middleware to ensure database session is properly managed.

    Note:
        The main session management is handled by get_db dependency.
        This middleware provides additional error handling and logging.
    """
    # Request ID for logging
    request_id = request.headers.get("X-Request-ID", "unknown")

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Request {request_id} failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Basic health check endpoint.

    Returns:
        API status information
    """
    return {
        "status": "healthy",
        "service": "media-analysis-api",
        "version": "1.0.0"
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check() -> dict:
    """
    Detailed health check including database connectivity.

    Returns:
        Comprehensive health status
    """
    from api.models.database import get_engine

    db_status = "unknown"
    try:
        engine = get_engine()
        if engine:
            connected = await verify_database_connection()
            db_status = "connected" if connected else "disconnected"
    except Exception:
        db_status = "error"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "media-analysis-api",
        "version": "1.0.0",
        "components": {
            "database": db_status
        }
    }


# =============================================================================
# Job API Endpoints
# =============================================================================

@app.get("/api/v1/jobs", response_model=JobListResponse, tags=["Jobs"])
async def list_jobs(
    *,
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> JobListResponse:
    """
    List all jobs with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Optional status filter
        repo: JobRepository dependency

    Returns:
        Paginated list of jobs
    """
    offset = (page - 1) * page_size

    if status:
        jobs = await repo.get_by_status(
            status=status,
            offset=offset,
            limit=page_size
        )
        total = await repo.get_by_status_count(status=status)
    else:
        jobs = await repo.get_all(offset=offset, limit=page_size)
        total = await repo.count()

    return JobListResponse(
        items=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(jobs)) < total
    )


@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job(
    job_id: str,
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> JobResponse:
    """
    Get a job by ID.

    Args:
        job_id: Job UUID
        repo: JobRepository dependency

    Returns:
        Job details
    """
    from uuid import UUID
    job = await repo.get_by_id(UUID(job_id))
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@app.post("/api/v1/jobs", response_model=JobResponse, status_code=201, tags=["Jobs"])
async def create_job(
    job_data: JobCreate,
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> JobResponse:
    """
    Create a new analysis job.

    Args:
        job_data: Job creation data
        repo: JobRepository dependency

    Returns:
        Created job details
    """
    job = await repo.create(
        status="pending",
        media_type=job_data.media_type.value,
        source_url=job_data.source_url,
        metadata_json=job_data.metadata_json
    )
    return JobResponse.model_validate(job)


@app.patch("/api/v1/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> JobResponse:
    """
    Update a job.

    Args:
        job_id: Job UUID
        job_update: Fields to update
        repo: JobRepository dependency

    Returns:
        Updated job details
    """
    from uuid import UUID
    from api.models.job import JobStatus

    update_data = job_update.model_dump(exclude_unset=True)

    # Handle enum conversion
    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"].value

    job = await repo.update(UUID(job_id), **update_data)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@app.delete("/api/v1/jobs/{job_id}", status_code=204, tags=["Jobs"])
async def delete_job(
    job_id: str,
    soft: bool = True,
    repo: JobRepository = Depends(JobRepositoryDependency)
):
    """
    Delete a job.

    Args:
        job_id: Job UUID
        soft: If True, soft delete (default); if True, hard delete
        repo: JobRepository dependency
    """
    from uuid import UUID
    from fastapi import HTTPException

    deleted = await repo.delete(UUID(job_id), soft=soft)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")


@app.post("/api/v1/jobs/{job_id}/processing", response_model=JobResponse, tags=["Jobs"])
async def mark_job_processing(
    job_id: str,
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> JobResponse:
    """
    Mark a job as processing.

    Args:
        job_id: Job UUID
        repo: JobRepository dependency

    Returns:
        Updated job details
    """
    from uuid import UUID
    from fastapi import HTTPException

    job = await repo.mark_as_processing(UUID(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@app.post("/api/v1/jobs/{job_id}/complete", response_model=JobResponse, tags=["Jobs"])
async def mark_job_completed(
    job_id: str,
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> JobResponse:
    """
    Mark a job as completed.

    Args:
        job_id: Job UUID
        repo: JobRepository dependency

    Returns:
        Updated job details
    """
    from uuid import UUID
    from fastapi import HTTPException

    job = await repo.mark_as_completed(UUID(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@app.post("/api/v1/jobs/{job_id}/fail", response_model=JobResponse, tags=["Jobs"])
async def mark_job_failed(
    job_id: str,
    error_message: str,
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> JobResponse:
    """
    Mark a job as failed.

    Args:
        job_id: Job UUID
        error_message: Error description
        repo: JobRepository dependency

    Returns:
        Updated job details
    """
    from uuid import UUID
    from fastapi import HTTPException

    job = await repo.mark_as_failed(UUID(job_id), error_message)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@app.get("/api/v1/jobs/pending", response_model=list[JobResponse], tags=["Jobs"])
async def get_pending_jobs(
    limit: int = 10,
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> list[JobResponse]:
    """
    Get pending jobs for processing.

    Args:
        limit: Maximum number of jobs to return
        repo: JobRepository dependency

    Returns:
        List of pending jobs
    """
    jobs = await repo.get_pending_jobs(limit=limit)
    return [JobResponse.model_validate(job) for job in jobs]


@app.get("/api/v1/jobs/statistics", tags=["Jobs"])
async def get_job_statistics(
    repo: JobRepository = Depends(JobRepositoryDependency)
) -> dict:
    """
    Get job statistics summary.

    Args:
        repo: JobRepository dependency

    Returns:
        Dictionary with counts by status
    """
    return await repo.get_statistics()


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    API root endpoint.

    Returns:
        API information
    """
    return {
        "name": "Media Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
