# MA-21 Research Findings

## Database Configuration Context

### Existing Infrastructure
- **Host**: af-postgres-1:5432
- **Database**: af-memory
- **User**: n8n
- **Network**: af-network (Docker external network)

### media-analysis-api Context
- **Service**: /opt/services/media-analysis/
- **Port**: 8000 (container), 8001 (host)
- **Network**: media-services-network (new)
- **Processing**: Video, audio, document branches

## Table Requirements Analysis

### media_analysis_requests
- **Purpose**: Track all analysis requests
- **Key Fields**:
  - UUID primary key (request_id)
  - media_type enum (video, audio, document, auto)
  - status enum (pending, processing, completed, failed, cancelled)
  - Timestamps (created_at, started_at, completed_at)
  - Processing metrics (processing_time_ms, confidence_score)
  - Error handling (error_message, error_details)
  - Provider chain tracking (provider_chain, api_costs)

### media_analysis_results
- **Purpose**: Store AI provider results
- **Key Fields**:
  - Foreign key to request_id
  - result_type enum (transcription, vision_analysis, etc.)
  - provider enum (minimax, deepgram, groq, openai, google, anthropic, internal)
  - content (text) and content_json (JSONB)
  - Cost tracking (token_count, cost_usd)

### media_files
- **Purpose**: Reference generated files
- **Key Fields**:
  - Foreign key to request_id
  - file_type enum (frame, contact_sheet, audio, etc.)
  - File metadata (file_size_bytes, width, height, mime_type)
  - Storage tracking (storage_location, remote_url)
  - Checksum for integrity

### contact_sheets
- **Purpose**: Store contact sheet metadata
- **Key Fields**:
  - Foreign keys to request_id and file_id
  - Grid configuration (grid_cols, grid_rows)
  - Frame tracking (frame_count, frames_per_sheet, sheet_number)
  - Dimensions (image_width, image_height)

## Index Strategy

### Critical Indexes (for status/created_at/request_id lookups)
1. `idx_media_requests_status` - Filter by status
2. `idx_media_requests_created_at` - Sort by date
3. `idx_media_requests_status_created` - Combined filter + sort
4. `idx_results_request_id` - Join performance
5. `idx_files_request_id` - File lookup by request

### Additional Indexes
6. `idx_media_requests_media_type` - Media type filter
7. `idx_results_result_type` - Result type filter
8. `idx_results_provider` - Provider filter
9. `idx_results_created_at` - Date sorting
10. `idx_files_file_type` - File type filter
11. `idx_files_mime_type` - MIME type filter
12. `idx_contact_sheets_request_id` - Contact sheet lookup
13. `idx_contact_sheets_file_id` - File reference lookup

## Implementation Findings

### Phase 1: Connection Setup
- Environment variables needed: DATABASE_URL, SYNC_DATABASE_URL
- Pool settings: pool_size=5, max_overflow=10

### Phase 2: Table Creation
- 4 tables with proper foreign key constraints
- 14 indexes for query optimization
- JSONB columns for flexible metadata

### Phase 3: ORM Layer
- SQLAlchemy models with relationships
- Async session support for FastAPI
- Repository pattern for data access

### Phase 4: API Integration
- Dependency injection for database sessions
- Automatic request tracking on endpoints
- Error handling with database rollback

### Phase 5: Query Endpoints
- GET /api/media/status/{request_id}
- GET /api/media/requests with filters

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Connection failure | Retry with exponential backoff |
| Query performance | Proper indexes + pagination |
| Data inconsistency | Database transactions + cascade |
| Storage bloat | Cleanup job for old records |
| Concurrent conflicts | Database locking |

## Key Learnings
1. Use UUIDs for request_id to support distributed systems
2. JSONB columns allow flexible metadata without schema changes
3. Cascade delete ensures data consistency when requests are removed
4. Provider chain tracking enables cost analysis and fallback debugging
5. Contact sheets link to both request and file for full traceability
