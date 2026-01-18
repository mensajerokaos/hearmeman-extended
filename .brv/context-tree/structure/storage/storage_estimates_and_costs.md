## Relations
@structure/storage/r2_storage_sync_system.md

## Raw Concept
**Task:**
Document Storage Estimates and Costs

**Changes:**
- Provides cost analysis and capacity planning for R2 storage usage

**Files:**
- docker/upload_to_r2.py

**Flow:**
N/A (Economic Analysis)

**Timestamp:** 2026-01-18

## Narrative
### Features
- Storage cost: $0.015 / GB-month (first 10GB free)
- Class A ops (PUT/COPY): $4.50 / million
- Typical output sizes: Image (1-6MB), Video (20-100MB), Audio (0.1-2MB)
- Estimation formula: StorageCost = stored_GB * 0.015; ClassACost = (uploads / 1M) * 4.50
- Retention planning: No automated cleanup; rolling window recommended
