# Endpoint Integration Plan

**Date**: 2026-01-20
**Task**: Database Integration PRD Research - Phase 3
**Output**: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24-pre/research/endpoint-integration.md

---

## 1. POST /api/media/analyze

### Current Implementation
- **File**: `/opt/services/media-analysis/routes/analyze.py` (new)
- **Lines**: N/A (new endpoint)
- **Current behavior**: Does not exist - this is a NEW endpoint
- **Request schema**: `AnalyzeRequest` Pydantic model
- **Response schema**: `AnalysisResponse` with analysis_id, status, estimated_time

### Required Changes

1. **Add Dependencies**
   - `AnalysisRepository` for database operations
   - `process_analysis` Celery task
   - `estimate_processing_time` utility

2. **Create Database Record**
   - INSERT into `analysis_request` with status='pending'
   - Store request parameters in JSONB columns
   - Generate UUID for analysis_id

3. **Queue Async Task**
   - Call `process_analysis.delay(analysis_id)`
   - Store Celery task ID for status tracking

4. **Return Response**
   - analysis_id (UUID)
   - status='pending'
   - estimated_time (seconds)

### New Dependencies

```txt
# requirements.txt
celery[redis]>=5.3.0
redis>=5.0.0
sqlalchemy[asyncio]>=2.0.0
psycopg2-binary>=2.9.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

### Code Changes

**File**: `/opt/services/media-analysis/routes/analyze.py`

```python
"""
POST /api/media/analyze - Create new analysis request

This endpoint accepts media URLs and prompts, creates database records,
and queues async processing tasks.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_repository, get_current_user
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalyzeRequest, AnalysisResponse
from app.tasks.process_analysis import process_analysis
from app.utils.estimation import estimate_processing_time


router = APIRouter(prefix="/api/media", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    """Request to analyze media."""
    prompt: str = Field(..., min_length=1, max_length=5000, description="Natural language instruction")
    media_url: str = Field(..., min_length=1, max_length=2000, description="Media URL to analyze")
    media_type: Optional[str] = Field(None, pattern="^(video|audio|document|image|auto)$")
    config: Optional[dict] = None
    options: Optional[dict] = None


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create new media analysis request",
    description="""
    Submit a media URL and natural language prompt for analysis.

    The request is queued for async processing. Use the returned
    analysis_id to check status and retrieve results.

    **Processing time estimates:**
    - Video (1 min): ~30 seconds
    - Video (10 min): ~2 minutes
    - Audio (1 min): ~10 seconds
    - Document: ~5 seconds
    """,
    responses={
        202: {
            "description": "Analysis request accepted",
            "content": {
                "application/json": {
                    "example": {
                        "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "pending",
                        "estimated_time": 30,
                        "message": "Analysis queued. Check status with /api/media/status/{id}"
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def analyze_media(
    request: AnalyzeRequest,
    repository: AnalysisRepository = Depends(get_repository),
    current_user: Optional[dict] = Depends(get_current_user),
) -> AnalysisResponse:
    """
    Create a new media analysis request.

    Steps:
    1. Validate request parameters
    2. Create database record with status='pending'
    3. Queue async processing task
    4. Return analysis_id and estimated time
    """
    # Step 1: Validate request
    if not request.media_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="media_url must start with http:// or https://"
        )

    # Step 2: Create database record
    analysis_id = uuid4()

    # Estimate processing time
    estimated_time = estimate_processing_time(
        media_type=request.media_type or 'auto',
        media_url=request.media_url,
    )

    # Create record in database
    analysis = await repository.create(
        request=request,
        celery_task_id=None,  # Will be set by Celery
        created_by=current_user.get('id') if current_user else None,
    )

    # Step 3: Queue async task
    celery_task = process_analysis.delay(str(analysis_id))

    # Update with Celery task ID
    await repository.update_celery_task_id(analysis_id, celery_task.id)

    # Step 4: Return response
    return AnalysisResponse(
        analysis_id=analysis_id,
        status='pending',
        estimated_time=estimated_time,
        message="Analysis queued. Check status with /api/media/status/{id}"
    )
```

**File**: `/opt/services/media-analysis/tasks/process_analysis.py`

```python
"""
Celery task for async media processing.
"""
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
import logging

from app.core.database import get_session
from app.repositories.analysis_repository import AnalysisRepository
from app.services.audio import AudioAnalysisService
from app.services.video import VideoAnalysisService
from app.services.document import DocumentAnalysisService


logger = logging.getLogger(__name__)

# Celery app instance
celery_app = Celery(
    "media_analysis",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def process_analysis(self, analysis_id: str):
    """
    Process media analysis asynchronously.

    Args:
        analysis_id: UUID of the analysis request

    This task:
    1. Fetches analysis request from database
    2. Updates status to 'processing'
    3. Routes to appropriate service (audio/video/document)
    4. Stores results
    5. Updates status to 'completed' or 'failed'
    """
    logger.info(f"Starting analysis {analysis_id}")

    async def _process():
        async for session in get_session():
            repository = AnalysisRepository(session)

            # Fetch request
            analysis = await repository.get_by_id(analysis_id)
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return

            # Update status to processing
            await repository.update_status(
                analysis_id,
                status='processing',
                progress=10,
            )

            try:
                # Route to appropriate service
                if analysis.media_type == 'video':
                    service = VideoAnalysisService()
                    results = await service.process(analysis)
                elif analysis.media_type == 'audio':
                    service = AudioAnalysisService()
                    results = await service.process(analysis)
                elif analysis.media_type == 'document':
                    service = DocumentAnalysisService()
                    results = await service.process(analysis)
                else:
                    # Auto-detect media type
                    service = VideoAnalysisService()  # Default
                    results = await service.process(analysis)

                # Update with results
                await repository.update_status(
                    analysis_id,
                    status='completed',
                    progress=100,
                    results=results,
                )

                logger.info(f"Analysis {analysis_id} completed successfully")

            except Exception as e:
                logger.error(f"Analysis {analysis_id} failed: {str(e)}")

                await repository.update_status(
                    analysis_id,
                    status='failed',
                    error_message=str(e),
                )

                raise

    # Run async task
    import asyncio
    asyncio.run(_process())
```

### Test Cases

```python
# File: /opt/services/media-analysis/tests/test_analyze_endpoint.py

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.schemas.analysis import AnalyzeRequest


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_repository():
    repository = AsyncMock()
    repository.create = AsyncMock()
    repository.update_celery_task_id = AsyncMock()
    return repository


class TestAnalyzeEndpoint:
    """Test cases for POST /api/media/analyze"""

    def test_successful_analysis_creation(self, client, mock_repository):
        """Test successful analysis request creation."""
        with patch('app.routes.analyze.get_repository', return_value=mock_repository):
            response = client.post(
                "/api/media/analyze",
                json={
                    "prompt": "What is happening in this video?",
                    "media_url": "https://example.com/video.mp4",
                    "media_type": "video",
                }
            )

            assert response.status_code == 202
            data = response.json()
            assert "analysis_id" in data
            assert data["status"] == "pending"
            assert "estimated_time" in data

    def test_invalid_media_url(self, client):
        """Test validation error for invalid media URL."""
        response = client.post(
            "/api/media/analyze",
            json={
                "prompt": "Analyze this",
                "media_url": "not-a-url",
            }
        )

        assert response.status_code == 400
        assert "media_url must start with http" in response.json()["detail"]

    def test_missing_required_field(self, client):
        """Test validation error for missing required fields."""
        response = client.post(
            "/api/media/analyze",
            json={
                "media_url": "https://example.com/video.mp4",
            }
        )

        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(e["loc"] == ["body", "prompt"] for e in errors)

    def test_empty_prompt(self, client):
        """Test validation error for empty prompt."""
        response = client.post(
            "/api/media/analyze",
            json={
                "prompt": "",
                "media_url": "https://example.com/video.mp4",
            }
        )

        assert response.status_code == 422

    def test_database_error_handling(self, client, mock_repository):
        """Test handling of database errors."""
        mock_repository.create.side_effect = Exception("Database connection failed")

        with patch('app.routes.analyze.get_repository', return_value=mock_repository):
            response = client.post(
                "/api/media/analyze",
                json={
                    "prompt": "Analyze this",
                    "media_url": "https://example.com/video.mp4",
                }
            )

            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]
```

---

## 2. GET /api/media/status/{id}

### Current Implementation
- **File**: `/opt/services/media-analysis/routes/status.py` (new)
- **Lines**: N/A (new endpoint)
- **Current behavior**: Does not exist
- **Required behavior**: Query database, return status, progress, and results

### Required Changes

1. **Query Database**
   - SELECT from `analysis_request` WHERE id={id}
   - Filter by status != 'deleted'

2. **Return Response**
   - Status (pending/processing/completed/failed)
   - Progress percentage
   - Results summary (if completed)
   - Error message (if failed)

3. **Error Handling**
   - 404: Analysis not found
   - 410: Analysis was deleted

### Code Changes

**File**: `/opt/services/media-analysis/routes/status.py`

```python
"""
GET /api/media/status/{id} - Get analysis status

Retrieve current status and results of an analysis request.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_repository
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisStatusResponse


router = APIRouter(prefix="/api/media", tags=["analysis"])


class StatusResponse(BaseModel):
    """Response for status query."""
    analysis_id: str
    status: str
    progress: int
    media_type: str
    source_url: str
    created_at: str
    updated_at: str
    completed_at: str | None
    result_summary: dict | None
    error_message: str | None


@router.get(
    "/status/{analysis_id}",
    response_model=StatusResponse,
    summary="Get analysis status",
    description="""
    Retrieve the current status and results of an analysis request.

    **Status values:**
    - `pending`: Request received, waiting to start
    - `processing`: Currently being processed
    - `completed`: Analysis finished successfully
    - `failed`: Analysis failed with error

    **Progress values:**
    - 0-99: Processing in progress
    - 100: Completed
    - N/A: Failed or pending
    """,
    responses={
        200: {"description": "Analysis status retrieved successfully"},
        404: {"description": "Analysis not found"},
        410: {"description": "Analysis was deleted"},
    },
)
async def get_status(
    analysis_id: str,
    repository: AnalysisRepository = Depends(get_repository),
) -> StatusResponse:
    """
    Get the status of an analysis request.

    Returns current processing status, progress percentage,
    and results if available.
    """
    # Validate UUID format
    try:
        uuid_id = UUID(analysis_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis_id format. Must be a valid UUID."
        )

    # Fetch from database
    analysis = await repository.get_by_id(uuid_id)

    if not analysis:
        # Check if deleted
        deleted = await repository.is_deleted(uuid_id)
        if deleted:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Analysis {analysis_id} was deleted"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found"
            )

    # Format response
    return StatusResponse(
        analysis_id=str(analysis.id),
        status=analysis.status,
        progress=analysis.progress,
        media_type=analysis.media_type,
        source_url=analysis.source_url,
        created_at=analysis.created_at.isoformat(),
        updated_at=analysis.updated_at.isoformat(),
        completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None,
        result_summary=analysis.results if analysis.status == 'completed' else None,
        error_message=analysis.error_message if analysis.status == 'failed' else None,
    )
```

### Test Cases

```python
# File: /opt/services/media-analysis/tests/test_status_endpoint.py

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.analysis_request import AnalysisRequest


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_repository():
    repository = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.is_deleted = AsyncMock(return_value=False)
    return repository


class TestStatusEndpoint:
    """Test cases for GET /api/media/status/{id}"""

    def test_get_pending_status(self, client, mock_repository):
        """Test getting status of pending analysis."""
        analysis_id = uuid4()
        mock_analysis = AnalysisRequest(
            id=analysis_id,
            status='pending',
            media_type='video',
            source_url='https://example.com/video.mp4',
            progress=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None,
            results={},
            error_message=None,
        )
        mock_repository.get_by_id.return_value = mock_analysis

        with patch('app.routes.status.get_repository', return_value=mock_repository):
            response = client.get(f"/api/media/status/{analysis_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["progress"] == 0

    def test_get_processing_status(self, client, mock_repository):
        """Test getting status of processing analysis."""
        analysis_id = uuid4()
        mock_analysis = AnalysisRequest(
            id=analysis_id,
            status='processing',
            media_type='video',
            source_url='https://example.com/video.mp4',
            progress=45,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None,
            results={},
            error_message=None,
        )
        mock_repository.get_by_id.return_value = mock_analysis

        with patch('app.routes.status.get_repository', return_value=mock_repository):
            response = client.get(f"/api/media/status/{analysis_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            assert data["progress"] == 45

    def test_get_completed_status(self, client, mock_repository):
        """Test getting status of completed analysis with results."""
        analysis_id = uuid4()
        mock_analysis = AnalysisRequest(
            id=analysis_id,
            status='completed',
            media_type='video',
            source_url='https://example.com/video.mp4',
            progress=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            results={"summary": "Video shows a person speaking"},
            error_message=None,
        )
        mock_repository.get_by_id.return_value = mock_analysis

        with patch('app.routes.status.get_repository', return_value=mock_repository):
            response = client.get(f"/api/media/status/{analysis_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["progress"] == 100
            assert "summary" in data["result_summary"]

    def test_get_failed_status(self, client, mock_repository):
        """Test getting status of failed analysis with error."""
        analysis_id = uuid4()
        mock_analysis = AnalysisRequest(
            id=analysis_id,
            status='failed',
            media_type='video',
            source_url='https://example.com/video.mp4',
            progress=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            results={},
            error_message="Failed to download media: 404 Not Found",
        )
        mock_repository.get_by_id.return_value = mock_analysis

        with patch('app.routes.status.get_repository', return_value=mock_repository):
            response = client.get(f"/api/media/status/{analysis_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert "404 Not Found" in data["error_message"]

    def test_not_found_status(self, client, mock_repository):
        """Test 404 for non-existent analysis."""
        analysis_id = uuid4()
        mock_repository.get_by_id.return_value = None
        mock_repository.is_deleted.return_value = False

        with patch('app.routes.status.get_repository', return_value=mock_repository):
            response = client.get(f"/api/media/status/{analysis_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_deleted_status(self, client, mock_repository):
        """Test 410 for deleted analysis."""
        analysis_id = uuid4()
        mock_repository.get_by_id.return_value = None
        mock_repository.is_deleted.return_value = True

        with patch('app.routes.status.get_repository', return_value=mock_repository):
            response = client.get(f"/api/media/status/{analysis_id}")

            assert response.status_code == 410
            assert "deleted" in response.json()["detail"]

    def test_invalid_uuid_format(self, client):
        """Test 400 for invalid UUID format."""
        response = client.get("/api/media/status/not-a-valid-uuid")

        assert response.status_code == 400
        assert "Invalid analysis_id format" in response.json()["detail"]
```

---

## 3. DELETE /api/media/{id}

### Current Implementation
- **File**: `/opt/services/media-analysis/routes/delete.py` (new)
- **Lines**: N/A (new endpoint)
- **Current behavior**: Does not exist
- **Required behavior**: Soft delete (UPDATE status='deleted')

### Required Changes

1. **Update Status**
   - UPDATE `analysis_request` SET status='deleted', deleted_at=NOW()
   - WHERE id={id} AND status != 'deleted'

2. **Return Response**
   - 204 No Content on success

3. **Cascade Rules**
   - No cascade - soft delete only
   - Related Celery tasks continue processing
   - Results preserved for audit

### Code Changes

**File**: `/opt/services/media-analysis/routes/delete.py`

```python
"""
DELETE /api/media/{id} - Soft delete analysis request

Mark an analysis request as deleted without removing data.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.dependencies import get_repository
from app.repositories.analysis_repository import AnalysisRepository


router = APIRouter(prefix="/api/media", tags=["analysis"])


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete analysis request",
    description="""
    Soft delete an analysis request.

    This marks the request as deleted without removing it from the database.
    The request will no longer appear in history or status queries.

    **Note:** This action cannot be undone. The data is retained for audit
    purposes but is filtered from all API responses.
    """,
    responses={
        204: {"description": "Analysis deleted successfully"},
        404: {"description": "Analysis not found"},
        410: {"description": "Analysis already deleted"},
    },
)
async def delete_analysis(
    analysis_id: str,
    repository: AnalysisRepository = Depends(get_repository),
) -> Response:
    """
    Soft delete an analysis request.

    Updates status to 'deleted' and sets deleted_at timestamp.
    """
    # Validate UUID format
    try:
        uuid_id = UUID(analysis_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis_id format. Must be a valid UUID."
        )

    # Check if exists and not already deleted
    analysis = await repository.get_by_id(uuid_id)

    if not analysis:
        deleted = await repository.is_deleted(uuid_id)
        if deleted:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Analysis {analysis_id} is already deleted"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found"
            )

    # Perform soft delete
    success = await repository.soft_delete(uuid_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis"
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### Test Cases

```python
# File: /opt/services/media-analysis/tests/test_delete_endpoint.py

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_repository():
    repository = AsyncMock()
    repository.get_by_id = AsyncMock()
    repository.is_deleted = AsyncMock(return_value=False)
    repository.soft_delete = AsyncMock(return_value=True)
    return repository


class TestDeleteEndpoint:
    """Test cases for DELETE /api/media/{id}"""

    def test_successful_deletion(self, client, mock_repository):
        """Test successful soft delete."""
        analysis_id = uuid4()
        mock_repository.get_by_id.return_value = True  # Exists

        with patch('app.routes.delete.get_repository', return_value=mock_repository):
            response = client.delete(f"/api/media/{analysis_id}")

            assert response.status_code == 204
            mock_repository.soft_delete.assert_called_once_with(analysis_id)

    def test_not_found_deletion(self, client, mock_repository):
        """Test 404 when deleting non-existent analysis."""
        analysis_id = uuid4()
        mock_repository.get_by_id.return_value = None
        mock_repository.is_deleted.return_value = False

        with patch('app.routes.delete.get_repository', return_value=mock_repository):
            response = client.delete(f"/api/media/{analysis_id}")

            assert response.status_code == 404

    def test_already_deleted(self, client, mock_repository):
        """Test 410 when deleting already deleted analysis."""
        analysis_id = uuid4()
        mock_repository.get_by_id.return_value = None
        mock_repository.is_deleted.return_value = True

        with patch('app.routes.delete.get_repository', return_value=mock_repository):
            response = client.delete(f"/api/media/{analysis_id}")

            assert response.status_code == 410

    def test_invalid_uuid_format(self, client):
        """Test 400 for invalid UUID format."""
        response = client.delete("/api/media/not-a-valid-uuid")

        assert response.status_code == 400
```

---

## 4. GET /api/media/history

### Current Implementation
- **File**: `/opt/services/media-analysis/routes/history.py` (new)
- **Lines**: N/A (new endpoint)
- **Current behavior**: Does not exist
- **Required behavior**: Paginated list with filters

### Required Changes

1. **Query with Filters**
   - Status filter (pending/processing/completed/failed/all)
   - Media type filter (video/audio/document/image/all)
   - Date range filter
   - Sort by (created_at/status/media_type)
   - Order (asc/desc)

2. **Pagination**
   - Page number (1-indexed)
   - Items per page (max 100)

3. **Return Response**
   - List of {id, status, media_type, created_at, prompt}
   - Pagination metadata

### Code Changes

**File**: `/opt/services/media-analysis/routes/history.py`

```python
"""
GET /api/media/history - List analysis history

Retrieve paginated list of analysis requests with filtering.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import get_repository, get_current_user
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisHistoryResponse, AnalysisHistoryItem


router = APIRouter(prefix="/api/media", tags=["analysis"])


class PaginationParams:
    """Query parameters for pagination."""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.per_page = per_page


class FilterParams:
    """Query parameters for filtering."""
    def __init__(
        self,
        status: Optional[str] = Query(None, pattern="^(pending|processing|completed|failed|all)$"),
        media_type: Optional[str] = Query(None, pattern="^(video|audio|document|image|all)$"),
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: str = Query("created_at", pattern="^(created_at|status|media_type)$"),
        order: str = Query("desc", pattern="^(asc|desc)$"),
    ):
        self.status = status
        self.media_type = media_type
        self.date_from = date_from
        self.date_to = date_to
        self.sort_by = sort_by
        self.order = order


@router.get(
    "/history",
    response_model=AnalysisHistoryResponse,
    summary="List analysis history",
    description="""
    Retrieve a paginated list of analysis requests with filtering.

    **Filtering:**
    - Status: Filter by processing status
    - Media type: Filter by media type
    - Date range: Filter by creation date
    - Sort: Order by created_at, status, or media_type

    **Pagination:**
    - Page: 1-indexed page number
    - Per page: Items per page (max 100)
    """,
    responses={
        200: {"description": "History retrieved successfully"},
        400: {"description": "Invalid query parameters"},
    },
)
async def get_history(
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    repository: AnalysisRepository = Depends(get_repository),
    current_user: Optional[dict] = Depends(get_current_user),
) -> AnalysisHistoryResponse:
    """
    Get paginated analysis history.

    Returns list of analysis requests matching filters.
    """
    # Build query parameters
    query_params = {
        'page': pagination.page,
        'per_page': pagination.per_page,
        'status': filters.status,
        'media_type': filters.media_type,
        'date_from': filters.date_from,
        'date_to': filters.date_to,
        'sort_by': filters.sort_by,
        'order': filters.order,
    }

    # Fetch from database
    analyses, total = await repository.get_history(
        filters=query_params,
        created_by=current_user.get('id') if current_user else None,
    )

    # Calculate pagination metadata
    total_pages = (total + pagination.per_page - 1) // pagination.per_page

    # Build response
    items = [
        AnalysisHistoryItem(
            analysis_id=a.id,
            status=a.status,
            media_type=a.media_type,
            prompt=a.analysis_config.get('prompt', '') if a.analysis_config else '',
            created_at=a.created_at,
            completed_at=a.completed_at,
        )
        for a in analyses
    ]

    return AnalysisHistoryResponse(
        data=items,
        pagination={
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': total,
            'total_pages': total_pages,
        }
    )
```

### Test Cases

```python
# File: /opt/services/media-analysis/tests/test_history_endpoint.py

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.analysis_request import AnalysisRequest


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_repository():
    repository = AsyncMock()
    repository.get_history = AsyncMock(return_value=([], 0))
    return repository


class TestHistoryEndpoint:
    """Test cases for GET /api/media/history"""

    def test_get_history_default(self, client, mock_repository):
        """Test default history query."""
        analysis_id = uuid4()
        mock_repository.get_history.return_value = (
            [
                AnalysisRequest(
                    id=analysis_id,
                    status='completed',
                    media_type='video',
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    analysis_config={'prompt': 'Analyze this'},
                )
            ],
            1
        )

        with patch('app.routes.history.get_repository', return_value=mock_repository):
            response = client.get("/api/media/history")

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "pagination" in data
            assert data["pagination"]["total"] == 1

    def test_get_history_with_filters(self, client, mock_repository):
        """Test history query with status filter."""
        with patch('app.routes.history.get_repository', return_value=mock_repository):
            response = client.get(
                "/api/media/history",
                params={
                    "status": "completed",
                    "media_type": "video",
                    "page": 1,
                    "per_page": 10,
                }
            )

            assert response.status_code == 200

    def test_get_history_pagination(self, client, mock_repository):
        """Test pagination parameters."""
        mock_repository.get_history.return_value = ([], 100)

        with patch('app.routes.history.get_repository', return_value=mock_repository):
            response = client.get(
                "/api/media/history",
                params={"page": 2, "per_page": 25}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["pagination"]["page"] == 2
            assert data["pagination"]["per_page"] == 25
            assert data["pagination"]["total"] == 100
            assert data["pagination"]["total_pages"] == 4

    def test_get_history_invalid_page(self, client):
        """Test invalid page number."""
        response = client.get(
            "/api/media/history",
            params={"page": 0}
        )

        assert response.status_code == 422

    def test_get_history_max_per_page(self, client, mock_repository):
        """Test max per_page limit."""
        with patch('app.routes.history.get_repository', return_value=mock_repository):
            response = client.get(
                "/api/media/history",
                params={"per_page": 200}  # Over max of 100
            )

            assert response.status_code == 422
```

---

## 5. New Files Required

| File | Purpose | Content |
|------|---------|---------|
| `/opt/services/media-analysis/routes/analyze.py` | POST /api/media/analyze | Endpoint + request validation |
| `/opt/services/media-analysis/routes/status.py` | GET /api/media/status/{id} | Status endpoint |
| `/opt/services/media-analysis/routes/delete.py` | DELETE /api/media/{id} | Delete endpoint |
| `/opt/services/media-analysis/routes/history.py` | GET /api/media/history | History endpoint |
| `/opt/services/media-analysis/repositories/analysis_repository.py` | Data access layer | CRUD operations |
| `/opt/services/media-analysis/tasks/process_analysis.py` | Async task | Celery task |
| `/opt/services/media-analysis/dependencies.py` | FastAPI dependencies | Repository injection |
| `/opt/services/media-analysis/tests/test_analyze_endpoint.py` | Analyze tests | Unit tests |
| `/opt/services/media-analysis/tests/test_status_endpoint.py` | Status tests | Unit tests |
| `/opt/services/media-analysis/tests/test_delete_endpoint.py` | Delete tests | Unit tests |
| `/opt/services/media-analysis/tests/test_history_endpoint.py` | History tests | Unit tests |

---

## 6. Modified Files

| File | Changes | Lines |
|------|---------|-------|
| `/opt/services/media-analysis/main.py` | Add routes | +20 lines |
| `/opt/services/media-analysis/requirements.txt` | Add dependencies | +5 lines |
| `/opt/services/media-analysis/app/__init__.py` | Export routes | +5 lines |

---

*Research completed: 2026-01-20*
*Output: /home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/plan/media-analysis-ma-24-pre/research/endpoint-integration.md*
