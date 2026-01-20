---
task: PRD for File Storage Organization System for media-analysis-api
agent: hc (Claude Sonnet 4.5 fallback)
model: claude-sonnet-4-5-20250929
timestamp: 2026-01-20T05:40:00Z
status: completed
author: $USER
---

# Product Requirements Document: File Storage Organization System

## Document Information

| Attribute | Value |
|-----------|-------|
| PRD ID | media-analysis-ma-23 |
| Version | 1.0 |
| Created | 2026-01-20 |
| Status | Draft |
| Owner | Media Analysis Team |

---

## Executive Summary

This document specifies the requirements and implementation plan for a File Storage Organization System for the media-analysis-api service. The system will manage storage directories for uploaded media, extracted frames, generated contact sheets, and final outputs with configurable time-to-live (TTL) policies for automatic cleanup.

**Key Objectives**:
- Implement organized storage structure with categorized directories
- Create automated cleanup system with configurable retention periods
- Ensure safe file operations with comprehensive error handling
- Integrate with existing FastAPI application via scheduler
- Provide monitoring and metrics for storage management

**Business Value**:
- Prevents disk exhaustion from accumulated media files
- Reduces operational costs by automatically cleaning temporary files
- Improves system reliability with automated maintenance
- Provides visibility into storage usage patterns

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Media Analysis API                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Storage Management Module                ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           ││
│  │  │ Cleanup     │ │ File        │ │ Policy      │           ││
│  │  │ Scheduler   │ │ Operations  │ │ Engine      │           ││
│  │  │             │ │             │ │             │           ││
│  │  │ • APScheduler│ │ • pathlib   │ │ • TTL rules │           ││
│  │  │ • Cron      │ │ • shutil    │ │ • Quotas    │           ││
│  │  │ • Jobs      │ │ • send2trash│ │ • Priority  │           ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Storage Directories                      ││
│  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐       ││
│  │  │ uploads/ │ │ frames/  │ │contact-   │ │outputs/│       ││
│  │  │ (7d TTL) │ │ (30d)    │ │ sheets/   │ │(indef) │       ││
│  │  │          │ │          │ │(30d TTL)  │ │        │       ││
│  │  │  10GB    │ │  50GB    │ │  20GB     │ │ 100GB  │       ││
│  │  │  quota   │ │  quota   │ │  quota    │ │  quota │       ││
│  │  └──────────┘ └──────────┘ └───────────┘ └────────┘       ││
│  │                        temp/ (24h TTL)                     ││
│  │                        5GB quota                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Scheduler (APScheduler + Cron Fallback)  ││
│  │  ┌──────────────────────────────────────────────────────┐  ││
│  │  │ PRIMARY: APScheduler (in-app)                        │  ││
│  │  │ • Daily at 02:00 UTC                                 │  ││
│  │  │ • Configurable via config.yaml                       │  ││
│  │  │ • Job persistence via Redis (optional)               │  ││
│  │  └──────────────────────────────────────────────────────┘  ││
│  │  ┌──────────────────────────────────────────────────────┐  ││
│  │  │ FALLBACK: Cron (system-level)                        │  ││
│  │  │ • 0 2 * * * /opt/services/media-analysis/bin/cleanup │  ││
│  │  │ • Runs if APScheduler fails                          │  ││
│  │  │ • Logging to /var/log/                              │  ││
│  │  └──────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Monitoring & Metrics                     ││
│  │  • Prometheus metrics: storage_bytes, files_cleaned        ││
│  │  • Logs: /var/log/media-analysis/storage.log               ││
│  │  • Alerts: Disk space < 10%, Cleanup failures              ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| StorageManager | Core class for file operations and cleanup |
| CleanupScheduler | Manages scheduled cleanup jobs |
| PolicyEngine | Evaluates TTL rules and quotas |
| FileOperations | Safe file handling (pathlib, shutil) |
| MetricsCollector | Tracks storage usage and cleanup stats |

### Data Flow

```
1. File Creation
   Upload Service → storage/{category}/ → PolicyEngine logs creation

2. Cleanup Trigger (Daily 02:00 UTC)
   Scheduler → CleanupJob → StorageManager.get_old_files()

3. File Evaluation
   PolicyEngine → Check TTL → Check Quota → Check Priority

4. Deletion
   SafeDelete → send2trash (optional) → Metrics.update()

5. Monitoring
   StorageManager → MetricsCollector → Prometheus
```

---

## Storage Directory Structure

### Directory Layout

```
/opt/services/media-analysis/
├── storage/
│   ├── .gitkeep
│   ├── README.md
│   ├── uploads/                    # Raw user uploads
│   │   ├── .gitkeep
│   │   └── YYYY-MM-DD/
│   ├── frames/                     # Extracted video frames
│   │   ├── .gitkeep
│   │   └── video_id/
│   ├── contact-sheets/             # Generated contact sheets
│   │   ├── .gitkeep
│   │   └── YYYY-MM-DD/
│   ├── outputs/                    # Final processed outputs
│   │   ├── .gitkeep
│   │   └── YYYY-MM-DD/
│   └── temp/                       # Temporary processing files
│       ├── .gitkeep
│       └── processing_id/
├── api/
│   ├── __init__.py                 # Update exports
│   ├── storage.py                  # StorageManager class
│   └── scheduler.py                # Scheduler integration
├── config/
│   └── config.yaml                 # Configuration updates
└── bin/
    └── cleanup.sh                  # Cron fallback script
```

### Retention Policies

| Directory | TTL | Quota | Rationale |
|-----------|-----|-------|-----------|
| `uploads/` | 7 days (604800s) | 10GB | Raw uploads should be processed quickly |
| `frames/` | 30 days (2592000s) | 50GB | Needed for debugging and reprocessing |
| `contact-sheets/` | 30 days (2592000s) | 20GB | Reference thumbnails, low priority |
| `outputs/` | Indefinite (-1) | 100GB | Primary deliverables, business critical |
| `temp/` | 24 hours (86400s) | 5GB | Intermediate files, short-lived |

---

## Implementation Phases

### PHASE 1: Storage Directory Setup

**Objective**: Create directory structure and initialize storage layout.

#### 1.1 Create Directory Structure

**Commands**:
```bash
# Create all directories at once
mkdir -p /opt/services/media-analysis/storage/{uploads,frames,contact-sheets,outputs,temp}

# Create .gitkeep files to preserve empty directories
for dir in /opt/services/media-analysis/storage/*/; do
    touch "${dir}.gitkeep"
done

# Set permissions
chmod 755 /opt/services/media-analysis/storage -R

# Verify structure
tree /opt/services/media-analysis/storage -L 2
```

**Expected Output**:
```
/opt/services/media-analysis/storage/
├── .gitkeep
├── contact-sheets/
│   └── .gitkeep
├── frames/
│   └── .gitkeep
├── outputs/
│   └── .gitkeep
├── temp/
│   └── .gitkeep
└── uploads/
    └── .gitkeep
```

#### 1.2 Create Storage README.md

**File**: `/opt/services/media-analysis/storage/README.md`

```markdown
# Storage Directory

This directory contains all media files for the media-analysis-api service.

## Directory Purposes

| Directory | Purpose | TTL |
|-----------|---------|-----|
| `uploads/` | Raw user-uploaded media | 7 days |
| `frames/` | Extracted video frames | 30 days |
| `contact-sheets/` | Generated thumbnail sheets | 30 days |
| `outputs/` | Final processed outputs | Indefinite |
| `temp/` | Temporary processing files | 24 hours |

## Cleanup Schedule

- **Daily**: 02:00 UTC - Full cleanup run
- **Hourly**: Temp directory cleanup (if needed)
- **On-demand**: Manual cleanup via API endpoint

## Access Control

- All files: 644 (rw-r--r--)
- All directories: 755 (rwxr-xr-x)
- Owner: media:media

## Monitoring

- Storage usage: `GET /api/v1/storage/stats`
- Cleanup logs: `/var/log/media-analysis/storage.log`
- Metrics: Prometheus endpoint `/metrics`
```

#### 1.3 Update API Package Exports

**File**: `/opt/services/media-analysis/api/__init__.py`

```python
"""Media Analysis API Package."""

from api.storage import StorageManager
from api.scheduler import cleanup_scheduler

__all__ = [
    "StorageManager",
    "cleanup_scheduler",
]
```

#### 1.4 Verification Commands

```bash
# Verify directories exist
test -d /opt/services/media-analysis/storage/uploads && echo "uploads OK"
test -d /opt/services/media-analysis/storage/frames && echo "frames OK"
test -d /opt/services/media-analysis/storage/contact-sheets && echo "contact-sheets OK"
test -d /opt/services/media-analysis/storage/outputs && echo "outputs OK"
test -d /opt/services/media-analysis/storage/temp && echo "temp OK"

# Verify .gitkeep files
test -f /opt/services/media-analysis/storage/uploads/.gitkeep && echo "uploads/.gitkeep OK"
test -f /opt/services/media-analysis/storage/frames/.gitkeep && echo "frames/.gitkeep OK"

# Verify permissions
stat -c "%a %n" /opt/services/media-analysis/storage/*/

# Check disk space
df -h /opt/services/media-analysis/storage
```

#### 1.5 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Directory already exists with data | Low | High | Check before create, backup existing |
| Permission denied | Medium | High | Run as root or media user, check umask |
| Disk full during setup | Low | High | Check available space before creation |

---

### PHASE 2: Storage Management Module

**Objective**: Implement the StorageManager class with cleanup and stats methods.

#### 2.1 Create StorageManager Class

**File**: `/opt/services/media-analysis/api/storage.py`

```python
"""
Storage Management Module for media-analysis-api.

Provides file organization, cleanup operations, and storage monitoring.
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from send2trash import send2trash

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Storage configuration schema."""
    base_path: str = "/opt/services/media-analysis/storage"
    retention: Dict[str, int] = field(default_factory=lambda: {
        'temp': 86400,          # 24 hours
        'uploads': 604800,      # 7 days
        'contact_sheets': 2592000,  # 30 days
        'frames': 2592000,      # 30 days
        'outputs': -1           # Indefinite
    })
    cleanup: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'schedule': "0 2 * * *",
        'dry_run': False,
        'batch_size': 100,
        'use_trash': True
    })
    quotas: Dict[str, int] = field(default_factory=lambda: {
        'temp': 5 * 1024**3,       # 5GB
        'uploads': 10 * 1024**3,   # 10GB
        'contact_sheets': 20 * 1024**3,  # 20GB
        'frames': 50 * 1024**3,    # 50GB
        'outputs': 100 * 1024**3   # 100GB
    })


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""
    category: str
    files_removed: int
    bytes_freed: int
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class StorageStats:
    """Storage statistics."""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    file_counts: Dict[str, int]
    quota_status: Dict[str, Dict[str, int]]


class StorageManager:
    """
    Manages storage directories, cleanup operations, and monitoring.

    Attributes:
        config: Storage configuration
        base_path: Root storage directory
    """

    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize StorageManager with configuration."""
        self.config = config or StorageConfig()
        self.base_path = Path(self.config.base_path)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for category in self.config.retention.keys():
            directory = self.base_path / category
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    def _get_file_age(self, file_path: Path) -> float:
        """Get file age in seconds based on modification time."""
        if not file_path.exists():
            return 0.0
        return time.time() - file_path.stat().st_mtime

    def _should_delete(self, file_path: Path, category: str) -> bool:
        """Check if file should be deleted based on TTL policy."""
        retention_seconds = self.config.retention.get(category, -1)
        if retention_seconds < 0:
            return False  # Indefinite retention
        age = self._get_file_age(file_path)
        return age > retention_seconds

    def _is_over_quota(self, category: str) -> bool:
        """Check if category is over its storage quota."""
        quota = self.config.quotas.get(category, float('inf'))
        category_path = self.base_path / category
        if not category_path.exists():
            return False
        current_size = sum(
            f.stat().st_size for f in category_path.rglob("*") if f.is_file()
        )
        return current_size > quota

    def cleanup_temp(self, dry_run: Optional[bool] = None) -> CleanupResult:
        """Clean up temporary files older than 24 hours."""
        return self._cleanup_category("temp", dry_run)

    def cleanup_uploads(self, dry_run: Optional[bool] = None) -> CleanupResult:
        """Clean up uploaded files older than 7 days."""
        return self._cleanup_category("uploads", dry_run)

    def cleanup_contact_sheets(self, dry_run: Optional[bool] = None) -> CleanupResult:
        """Clean up contact sheets older than 30 days."""
        return self._cleanup_category("contact_sheets", dry_run)

    def cleanup_frames(self, dry_run: Optional[bool] = None) -> CleanupResult:
        """Clean up extracted frames older than 30 days."""
        return self._cleanup_category("frames", dry_run)

    def _cleanup_category(
        self, category: str, dry_run: Optional[bool] = None
    ) -> CleanupResult:
        """
        Clean up files in a category based on TTL policy.

        Args:
            category: Storage category (temp, uploads, frames, etc.)
            dry_run: If True, simulate cleanup without deleting

        Returns:
            CleanupResult with deletion statistics
        """
        start_time = time.time()
        dry_run = dry_run if dry_run is not None else self.config.cleanup.get('dry_run', False)

        category_path = self.base_path / category
        if not category_path.exists():
            return CleanupResult(
                category=category,
                files_removed=0,
                bytes_freed=0,
                duration_seconds=time.time() - start_time
            )

        files_to_delete = []
        total_bytes_freed = 0
        errors = []

        # Find files to delete
        for file_path in category_path.rglob("*"):
            if file_path.is_file():
                if self._should_delete(file_path, category):
                    files_to_delete.append(file_path)
                    total_bytes_freed += file_path.stat().st_size

        # Limit batch size
        batch_size = self.config.cleanup.get('batch_size', 100)
        files_to_delete = files_to_delete[:batch_size]

        logger.info(
            f"Cleanup {category}: {len(files_to_delete)} files, "
            f"{total_bytes_freed / 1024**2:.2f}MB, dry_run={dry_run}"
        )

        # Delete files
        use_trash = self.config.cleanup.get('use_trash', True)
        for file_path in files_to_delete:
            try:
                if dry_run:
                    logger.debug(f"[DRY RUN] Would delete: {file_path}")
                else:
                    if use_trash:
                        send2trash(str(file_path))
                    else:
                        file_path.unlink()
                    logger.debug(f"Deleted: {file_path}")
            except Exception as e:
                error_msg = f"Error deleting {file_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        return CleanupResult(
            category=category,
            files_removed=len(files_to_delete) if not dry_run else 0,
            bytes_freed=total_bytes_freed if not dry_run else 0,
            errors=errors,
            duration_seconds=time.time() - start_time
        )

    def run_cleanup(self, dry_run: Optional[bool] = None) -> Dict[str, CleanupResult]:
        """
        Run cleanup on all categories.

        Args:
            dry_run: If True, simulate cleanup without deleting

        Returns:
            Dictionary of category -> CleanupResult
        """
        if not self.config.cleanup.get('enabled', True):
            logger.info("Cleanup is disabled in configuration")
            return {}

        dry_run = dry_run if dry_run is not None else self.config.cleanup.get('dry_run', False)
        results = {}

        # Priority order: temp first, then others
        categories = ['temp', 'uploads', 'frames', 'contact_sheets']

        for category in categories:
            cleanup_method = getattr(self, f'cleanup_{category}', None)
            if cleanup_method:
                results[category] = cleanup_method(dry_run)
                logger.info(
                    f"Cleanup {category}: {results[category].files_removed} files, "
                    f"{results[category].bytes_freed / 1024**2:.2f}MB"
                )

        return results

    def get_storage_stats(self) -> StorageStats:
        """
        Get current storage statistics.

        Returns:
            StorageStats with usage and file counts
        """
        total_bytes = 0
        used_bytes = 0
        file_counts = {}
        quota_status = {}

        for category in self.config.retention.keys():
            category_path = self.base_path / category
            if category_path.exists():
                category_bytes = 0
                file_count = 0

                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        category_bytes += size
                        file_count += 1

                total_bytes += category_bytes
                file_counts[category] = file_count

                # Check quota
                quota = self.config.quotas.get(category, float('inf'))
                percent_used = (category_bytes / quota * 100) if quota > 0 else 0
                quota_status[category] = {
                    'used_bytes': category_bytes,
                    'quota_bytes': quota,
                    'percent_used': percent_used
                }

        # Get disk-level stats
        disk_usage = self._get_disk_usage()

        return StorageStats(
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            free_bytes=disk_usage.free,
            file_counts=file_counts,
            quota_status=quota_status
        )

    def _get_disk_usage(self):
        """Get disk usage for storage volume."""
        import psutil
        return psutil.disk_usage(str(self.base_path))

    def ensure_directories(self) -> Dict[str, bool]:
        """
        Ensure all storage directories exist with correct permissions.

        Returns:
            Dictionary of directory -> exists status
        """
        results = {}
        for category in self.config.retention.keys():
            directory = self.base_path / category
            directory.mkdir(parents=True, exist_ok=True)
            results[str(directory)] = directory.exists()
        return results

    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors.

        Returns:
            List of validation messages (empty = valid)
        """
        messages = []

        # Check base path
        if not self.base_path.exists():
            messages.append(f"WARNING: Base path {self.base_path} does not exist")
        elif not self.base_path.is_dir():
            messages.append(f"ERROR: Base path {self.base_path} is not a directory")

        # Check retention values
        for category, retention in self.config.retention.items():
            if retention < -1:
                messages.append(f"ERROR: Invalid retention for {category}: {retention}")
            if retention == 0:
                messages.append(f"WARNING: Retention for {category} is 0 (immediate deletion)")

        # Check quotas
        for category, quota in self.config.quotas.items():
            if quota < 0:
                messages.append(f"ERROR: Negative quota for {category}: {quota}")

        return messages
```

#### 2.2 Key Methods Documentation

| Method | Purpose | Parameters | Returns |
|--------|---------|------------|---------|
| `__init__` | Initialize StorageManager | config (optional) | - |
| `cleanup_temp` | Clean temp directory | dry_run (optional) | CleanupResult |
| `cleanup_uploads` | Clean uploads directory | dry_run (optional) | CleanupResult |
| `cleanup_frames` | Clean frames directory | dry_run (optional) | CleanupResult |
| `cleanup_contact_sheets` | Clean contact-sheets | dry_run (optional) | CleanupResult |
| `run_cleanup` | Clean all categories | dry_run (optional) | Dict[str, CleanupResult] |
| `get_storage_stats` | Get storage metrics | - | StorageStats |
| `ensure_directories` | Create directories | - | Dict[str, bool] |
| `validate_config` | Validate configuration | - | List[str] |

#### 2.3 Verification Commands

```bash
# Test Python syntax
python3 -m py_compile /opt/services/media-analysis/api/storage.py

# Test module import
cd /opt/services/media-analysis
source venv/bin/activate
python3 -c "
from api.storage import StorageManager, StorageConfig
config = StorageConfig()
manager = StorageManager(config)
print('StorageManager imported successfully')
print(f'Base path: {manager.base_path}')
print(f'Categories: {list(config.retention.keys())}')
"

# Test directory creation
python3 -c "
from api.storage import StorageManager
manager = StorageManager()
result = manager.ensure_directories()
print(f'Directories created: {result}')
"

# Check for errors
python3 -c "
from api.storage import StorageManager
manager = StorageManager()
errors = manager.validate_config()
if errors:
    print('Validation warnings/errors:')
    for msg in errors:
        print(f'  - {msg}')
else:
    print('Configuration valid')
"
```

#### 2.4 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Import errors (missing dependencies) | Medium | High | Add send2trash to requirements.txt |
| Permission errors during cleanup | Medium | High | Use send2trash, catch OSError |
| Large file operations timeout | Low | Medium | Batch processing (100 files/batch) |
| Incorrect TTL calculation | Low | Critical | Use time.time(), validate against clock |
| Quota calculation performance | Medium | Medium | Cache stats, update incrementally |

---

### PHASE 3: Configuration Schema

**Objective**: Define configuration structure for storage management.

#### 3.1 Configuration File Updates

**File**: `/opt/services/media-analysis/config/config.yaml`

Add the following configuration section:

```yaml
# Storage Configuration
storage:
  # Base path for all storage directories
  base_path: "/opt/services/media-analysis/storage"

  # Retention periods in seconds
  # -1 means indefinite retention
  retention:
    temp: 86400              # 24 hours
    uploads: 604800          # 7 days
    contact_sheets: 2592000  # 30 days
    frames: 2592000          # 30 days
    outputs: -1              # Indefinite

  # Storage quotas in bytes
  quotas:
    temp: 5368709120         # 5GB
    uploads: 10737418240     # 10GB
    contact_sheets: 21474836480  # 20GB
    frames: 53687091200      # 50GB
    outputs: 107374182400    # 100GB

  # Cleanup job configuration
  cleanup:
    enabled: true            # Enable/disable automatic cleanup
    schedule: "0 2 * * *"    # Cron schedule (daily at 02:00 UTC)
    dry_run: false           # When true, simulate cleanup only
    batch_size: 100          # Max files to process per batch
    use_trash: true          # Use OS trash instead of permanent delete

  # Monitoring configuration
  monitoring:
    log_level: "INFO"        # DEBUG, INFO, WARNING, ERROR
    metrics_enabled: true    # Expose Prometheus metrics
    alert_threshold_percent: 10  # Alert when free space < 10%
```

#### 3.2 Environment Variable Overrides

**File**: `/opt/services/media-analysis/config/schema.py`

```python
"""Configuration schema with environment variable overrides."""

import os
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class StorageConfig:
    """Storage configuration with env var overrides."""
    base_path: str = "/opt/services/media-analysis/storage"
    retention: Dict[str, int] = field(default_factory=lambda: {
        'temp': 86400,
        'uploads': 604800,
        'contact_sheets': 2592000,
        'frames': 2592000,
        'outputs': -1
    })
    cleanup: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'schedule': "0 2 * * *",
        'dry_run': False,
        'batch_size': 100,
        'use_trash': True
    })
    quotas: Dict[str, int] = field(default_factory=lambda: {
        'temp': 5 * 1024**3,
        'uploads': 10 * 1024**3,
        'contact_sheets': 20 * 1024**3,
        'frames': 50 * 1024**3,
        'outputs': 100 * 1024**3
    })

    def from_env(self) -> 'StorageConfig':
        """Load configuration from environment variables."""
        # Override base path
        if os.getenv('STORAGE_BASE_PATH'):
            self.base_path = os.getenv('STORAGE_BASE_PATH')

        # Override retention periods
        for key in self.retention.keys():
            env_key = f'STORAGE_RETENTION_{key.upper()}'
            if os.getenv(env_key):
                self.retention[key] = int(os.getenv(env_key))

        # Override quotas
        for key in self.quotas.keys():
            env_key = f'STORAGE_QUOTA_{key.upper()}'
            if os.getenv(env_key):
                self.quotas[key] = int(os.getenv(env_key))

        # Override cleanup settings
        if os.getenv('STORAGE_CLEANUP_ENABLED'):
            self.cleanup['enabled'] = os.getenv('STORAGE_CLEANUP_ENABLED').lower() == 'true'
        if os.getenv('STORAGE_CLEANUP_DRY_RUN'):
            self.cleanup['dry_run'] = os.getenv('STORAGE_CLEANUP_DRY_RUN').lower() == 'true'
        if os.getenv('STORAGE_CLEANUP_BATCH_SIZE'):
            self.cleanup['batch_size'] = int(os.getenv('STORAGE_CLEANUP_BATCH_SIZE'))

        return self
```

#### 3.3 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_BASE_PATH` | /opt/services/media-analysis/storage | Root storage directory |
| `STORAGE_RETENTION_TEMP` | 86400 | Temp TTL in seconds |
| `STORAGE_RETENTION_UPLOADS` | 604800 | Uploads TTL in seconds |
| `STORAGE_RETENTION_FRAMES` | 2592000 | Frames TTL in seconds |
| `STORAGE_RETENTION_CONTACT_SHEETS` | 2592000 | Contact-sheets TTL in seconds |
| `STORAGE_RETENTION_OUTPUTS` | -1 | Outputs TTL (-1 = indefinite) |
| `STORAGE_QUOTA_TEMP` | 5368709120 | Temp quota in bytes (5GB) |
| `STORAGE_QUOTA_UPLOADS` | 10737418240 | Uploads quota in bytes (10GB) |
| `STORAGE_QUOTA_FRAMES` | 53687091200 | Frames quota in bytes (50GB) |
| `STORAGE_QUOTA_CONTACT_SHEETS` | 21474836480 | Contact-sheets quota (20GB) |
| `STORAGE_QUOTA_OUTPUTS` | 107374182400 | Outputs quota in bytes (100GB) |
| `STORAGE_CLEANUP_ENABLED` | true | Enable/disable cleanup |
| `STORAGE_CLEANUP_DRY_RUN` | false | Simulate cleanup only |
| `STORAGE_CLEANUP_BATCH_SIZE` | 100 | Files per cleanup batch |

#### 3.4 Verification Commands

```bash
# Test configuration loading
cd /opt/services/media-analysis
source venv/bin/activate
python3 -c "
from config.schema import StorageConfig
import os

# Test defaults
config = StorageConfig()
print('Default config:')
print(f'  Base path: {config.base_path}')
print(f'  Temp retention: {config.retention[\"temp\"]}s')
print(f'  Uploads quota: {config.quotas[\"uploads\"] / 1024**3}GB')

# Test env override
os.environ['STORAGE_RETENTION_TEMP'] = '3600'
os.environ['STORAGE_QUOTA_TEMP'] = '1073741824'
config2 = StorageConfig().from_env()
print('\\nEnv override:')
print(f'  Temp retention: {config2.retention[\"temp\"]}s')
print(f'  Temp quota: {config2.quotas[\"temp\"] / 1024**3}GB')
"

# Validate YAML syntax
python3 -c "
import yaml
with open('/opt/services/media-analysis/config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)
if 'storage' in config:
    print('storage section valid')
    print(f\"Retention keys: {list(config['storage']['retention'].keys())}\")
    print(f\"Quota keys: {list(config['storage']['quotas'].keys())}\")
else:
    print('ERROR: storage section missing')
"
```

#### 3.5 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Invalid YAML syntax | Low | High | Validate with Python yaml.safe_load |
| Missing configuration section | Low | High | Provide defaults, validate on startup |
| Environment variable type errors | Medium | Medium | Type conversion with defaults |
| Path traversal vulnerabilities | Low | Critical | Validate paths, use pathlib |

---

### PHASE 4: Scheduler Integration

**Objective**: Integrate cleanup scheduler with FastAPI application.

#### 4.1 Create Scheduler Module

**File**: `/opt/services/media-analysis/api/scheduler.py`

```python
"""
Scheduler integration for storage cleanup.

Provides APScheduler integration with FastAPI lifespan and cron fallback.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.storage import StorageManager, StorageConfig

logger = logging.getLogger(__name__)


# Global scheduler instance
cleanup_scheduler = AsyncIOScheduler()
_storage_manager = None


def get_storage_manager() -> StorageManager:
    """Get or create StorageManager instance."""
    global _storage_manager
    if _storage_manager is None:
        config = StorageConfig()
        _storage_manager = StorageManager(config)
    return _storage_manager


def cleanup_job(dry_run: bool = False) -> dict:
    """
    Execute cleanup job for all storage categories.

    Args:
        dry_run: If True, simulate cleanup without deleting

    Returns:
        Dictionary with cleanup results
    """
    manager = get_storage_manager()
    start_time = datetime.utcnow()

    logger.info("Starting scheduled storage cleanup")

    try:
        results = manager.run_cleanup(dry_run=dry_run)

        # Summarize results
        total_files = sum(r.files_removed for r in results.values())
        total_bytes = sum(r.bytes_freed for r in results.values())

        summary = {
            'status': 'success',
            'start_time': start_time.isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'categories': {cat: {
                'files_removed': res.files_removed,
                'bytes_freed': res.bytes_freed,
                'errors': len(res.errors)
            } for cat, res in results.items()},
            'total_files_removed': total_files,
            'total_bytes_freed': total_bytes
        }

        logger.info(
            f"Storage cleanup completed: {total_files} files, "
            f"{total_bytes / 1024**2:.2f}MB freed"
        )

        return summary

    except Exception as e:
        logger.exception(f"Storage cleanup failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'start_time': start_time.isoformat()
        }


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan context manager for scheduler."""
    global cleanup_scheduler, _storage_manager

    # Initialize storage manager
    config = StorageConfig()
    _storage_manager = StorageManager(config)

    # Configure scheduler
    cleanup_scheduler = AsyncIOScheduler()

    # Add cleanup job - daily at 02:00 UTC
    cleanup_scheduler.add_job(
        cleanup_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_storage_cleanup',
        name='Daily storage cleanup',
        replace_existing=True,
        max_instances=1  # Prevent concurrent runs
    )

    logger.info("Starting cleanup scheduler")
    cleanup_scheduler.start()

    # Log next run time
    next_run = cleanup_scheduler.get_job('daily_storage_cleanup').next_run_time
    logger.info(f"Next cleanup scheduled for: {next_run}")

    yield

    # Shutdown
    logger.info("Shutting down cleanup scheduler")
    cleanup_scheduler.shutdown()


# Cron fallback script
CRON_SCRIPT = '''#!/bin/bash
# /opt/services/media-analysis/bin/cleanup.sh
# Fallback cleanup script when APScheduler is unavailable

cd /opt/services/media-analysis
source venv/bin/activate

python3 -c "
from api.storage import StorageManager, StorageConfig

config = StorageConfig()
manager = StorageManager(config)

# Check if we should do dry run (first Friday of month)
if [ \$(date +\%u) -eq 1 ] && [ \$(date +\%d) -le 7 ]; then
    dry_run=True
    echo \"Dry run mode (first week of month)\"
else
    dry_run=False
fi

result = manager.run_cleanup(dry_run=dry_run)
total_files = sum(r.files_removed for r in result.values())
total_bytes = sum(r.bytes_freed for r in result.values())

print(f'Cleanup complete: {total_files} files, {total_bytes / 1024**2:.2f}MB freed')
"
'''
```

#### 4.2 FastAPI Integration

**File**: `/opt/services/media-analysis/main.py` (excerpt)

```python
"""Main FastAPI application with storage scheduler."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from typing import Dict, Any

from api.storage import StorageManager, StorageConfig, CleanupResult, StorageStats
from api.scheduler import cleanup_scheduler, cleanup_job, get_storage_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup - scheduler is already started in scheduler.py
    yield
    # Shutdown
    cleanup_scheduler.shutdown()

app = FastAPI(lifespan=lifespan)


@app.get("/api/v1/storage/stats")
async def get_storage_stats() -> Dict[str, Any]:
    """Get current storage statistics."""
    manager = get_storage_manager()
    stats = manager.get_storage_stats()

    return {
        "total_bytes": stats.total_bytes,
        "used_bytes": stats.used_bytes,
        "free_bytes": stats.free_bytes,
        "file_counts": stats.file_counts,
        "quota_status": stats.quota_status
    }


@app.post("/api/v1/storage/cleanup")
async def trigger_cleanup(dry_run: bool = True) -> Dict[str, Any]:
    """
    Manually trigger cleanup job.

    Args:
        dry_run: If True, simulate without deleting

    Returns:
        Cleanup results
    """
    if not dry_run:
        # Require confirmation for non-dry-run
        return {"message": "Set dry_run=false to actually delete files", "dry_run": dry_run}

    return cleanup_job(dry_run=dry_run)


@app.get("/api/v1/storage/validate")
async def validate_storage() -> Dict[str, Any]:
    """Validate storage configuration."""
    manager = get_storage_manager()
    messages = manager.validate_config()

    return {
        "valid": len(messages) == 0,
        "messages": messages
    }
```

#### 4.3 Cron Fallback Setup

**Commands**:
```bash
# Create cron script
cat > /opt/services/media-analysis/bin/cleanup.sh << 'EOF'
#!/bin/bash
# /opt/services/media-analysis/bin/cleanup.sh
# Fallback cleanup script when APScheduler is unavailable

cd /opt/services/media-analysis
source venv/bin/activate

# Dry run on first week of month, actual cleanup otherwise
if [ $(date +%u) -eq 1 ] && [ $(date +%d) -le 7 ]; then
    dry_run=True
    echo "$(date): Dry run mode (first week of month)"
else
    dry_run=False
fi

python3 -c "
from api.storage import StorageManager, StorageConfig
config = StorageConfig()
manager = StorageManager(config)
result = manager.run_cleanup(dry_run=$dry_run)
total_files = sum(r.files_removed for r in result.values())
total_bytes = sum(r.bytes_freed for r in result.values())
print(f'Cleanup: {total_files} files, {total_bytes / 1024**2:.2f}MB freed')
"
EOF

# Make executable
chmod +x /opt/services/media-analysis/bin/cleanup.sh

# Add to crontab (edit with crontab -e)
echo "0 2 * * * /opt/services/media-analysis/bin/cleanup.sh >> /var/log/media-analysis/cleanup.log 2>&1" | crontab -

# Verify crontab
crontab -l
```

#### 4.4 Verification Commands

```bash
# Test scheduler import
cd /opt/services/media-analysis
source venv/bin/activate
python3 -c "
from api.scheduler import cleanup_scheduler, cleanup_job
print('Scheduler module imported successfully')

# Test cleanup job
result = cleanup_job(dry_run=True)
print(f'Cleanup job result: {result[\"status\"]}')
"

# Test FastAPI endpoints
curl -s http://localhost:8080/api/v1/storage/stats | python3 -m json.tool
curl -s http://localhost:8080/api/v1/storage/validate | python3 -m json.tool
curl -X POST -s http://localhost:8080/api/v1/storage/cleanup?dry_run=true | python3 -m json.tool

# Verify cron script
test -x /opt/services/media-analysis/bin/cleanup.sh && echo "Cron script executable"
bash -n /opt/services/media-analysis/bin/cleanup.sh && echo "Cron script syntax OK"
```

#### 4.5 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scheduler startup failure | Low | High | Graceful degradation, cron fallback |
| Concurrent cleanup runs | Medium | Medium | max_instances=1, file locking |
| App crash leaves cleanup undone | Medium | High | Cron fallback ensures execution |
| Job persistence across restarts | Low | Medium | Redis jobstore (optional) |
| Scheduler time zone issues | Medium | Medium | Use UTC explicitly in CronTrigger |

---

### PHASE 5: Testing & Verification

**Objective**: Ensure storage management works correctly through comprehensive testing.

#### 5.1 Unit Tests

**File**: `/opt/services/media-analysis/tests/test_storage.py`

```python
"""Unit tests for StorageManager."""

import os
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
import pytest

from api.storage import StorageManager, StorageConfig, CleanupResult


class TestStorageManager:
    """Test cases for StorageManager."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for testing."""
        temp_dir = tempfile.mkdtemp(prefix='media_test_')
        yield temp_dir
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def storage_manager(self, temp_storage):
        """Create StorageManager with temp directory."""
        config = StorageConfig(base_path=temp_storage)
        return StorageManager(config)

    def test_init_creates_directories(self, temp_storage):
        """Test that initialization creates required directories."""
        config = StorageConfig(base_path=temp_storage)
        manager = StorageManager(config)

        for category in config.retention.keys():
            assert (Path(temp_storage) / category).exists()

    def test_cleanup_temp_removes_old_files(self, storage_manager, temp_storage):
        """Test that temp files older than TTL are removed."""
        # Create a temp file
        temp_file = Path(temp_storage) / "temp" / "test_old.tmp"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_text("test content")

        # Set modification time to 25 hours ago
        old_time = time.time() - (25 * 3600)
        os.utime(temp_file, (old_time, old_time))

        # Run cleanup
        result = storage_manager.cleanup_temp(dry_run=False)

        assert result.category == "temp"
        assert result.files_removed >= 1
        assert not temp_file.exists()

    def test_cleanup_dry_run_does_not_delete(self, storage_manager, temp_storage):
        """Test that dry_run doesn't actually delete files."""
        # Create a temp file
        temp_file = Path(temp_storage) / "temp" / "test.tmp"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_text("test content")

        # Run cleanup in dry_run mode
        result = storage_manager.cleanup_temp(dry_run=True)

        assert result.files_removed == 0  # Not actually removed
        assert temp_file.exists()  # File still exists

    def test_cleanup_respects_indefinite_retention(self, storage_manager, temp_storage):
        """Test that outputs with -1 retention are never deleted."""
        # Create an output file
        output_file = Path(temp_storage) / "outputs" / "important.mp4"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("important content")

        # Set modification time to 100 years ago
        old_time = time.time() - (100 * 365 * 24 * 3600)
        os.utime(output_file, (old_time, old_time))

        # Run cleanup
        result = storage_manager.cleanup_outputs(dry_run=False)

        assert result.files_removed == 0
        assert output_file.exists()  # File preserved

    def test_get_storage_stats(self, storage_manager, temp_storage):
        """Test storage statistics calculation."""
        # Create some test files
        for i in range(5):
            test_file = Path(temp_storage) / "uploads" / f"test_{i}.jpg"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text(f"content {i}" * 1000)

        stats = storage_manager.get_storage_stats()

        assert stats.file_counts["uploads"] >= 5
        assert stats.total_bytes > 0
        assert "uploads" in stats.quota_status

    def test_validate_config_warns_on_zero_retention(self, temp_storage):
        """Test that zero retention generates warning."""
        config = StorageConfig(
            base_path=temp_storage,
            retention={'temp': 0}  # Immediate deletion
        )
        manager = StorageManager(config)
        messages = manager.validate_config()

        assert any("0" in msg for msg in messages)

    def test_batch_size_enforcement(self, storage_manager, temp_storage):
        """Test that batch_size limit is respected."""
        # Create many temp files
        for i in range(200):
            temp_file = Path(temp_storage) / "temp" / f"test_{i}.tmp"
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file.write_text(f"content {i}")

            # Set all to old
            old_time = time.time() - (25 * 3600)
            os.utime(temp_file, (old_time, old_time))

        # Run cleanup with batch_size=100
        result = storage_manager.cleanup_temp(dry_run=False)

        # Should be limited to batch_size
        assert result.files_removed <= storage_manager.config.cleanup['batch_size']


class TestFileAge:
    """Test file age calculation."""

    def test_file_age_calculation(self):
        """Test that file age is calculated correctly."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            # Set modification time to 1 hour ago
            old_time = time.time() - 3600
            os.utime(temp_path, (old_time, old_time))

            # Calculate age
            age = time.time() - os.path.getmtime(temp_path)

            # Should be approximately 1 hour (3600 seconds)
            assert 3500 < age < 3700
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

#### 5.2 Integration Tests

**File**: `/opt/services/media-analysis/tests/test_integration.py`

```python
"""Integration tests for storage with real filesystem."""

import pytest
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.storage import StorageManager, StorageConfig


class TestIntegration:
    """Integration tests with real storage."""

    @pytest.fixture
    def real_storage(self, tmp_path):
        """Create real storage directory."""
        storage_dir = tmp_path / "media_storage"
        storage_dir.mkdir()
        return str(storage_dir)

    @pytest.fixture
    def manager(self, real_storage):
        """Create manager with real storage."""
        config = StorageConfig(base_path=real_storage)
        return StorageManager(config)

    def test_full_cleanup_workflow(self, manager, real_storage):
        """Test complete cleanup workflow."""
        # 1. Create files in different categories
        categories = ['temp', 'uploads', 'frames', 'contact_sheets', 'outputs']

        for cat in categories:
            cat_dir = Path(real_storage) / cat
            cat_dir.mkdir(exist_ok=True)

            for i in range(3):
                file_path = cat_dir / f"test_{cat}_{i}.tmp"
                file_path.write_text(f"content {cat} {i}")

        # 2. Make temp files old
        for file_path in (Path(real_storage) / "temp").glob("*.tmp"):
            old_time = time.time() - (25 * 3600)
            os.utime(file_path, (old_time, old_time))

        # 3. Run cleanup
        results = manager.run_cleanup(dry_run=False)

        # 4. Verify temp files deleted
        assert results['temp'].files_removed >= 3
        assert not any((Path(real_storage) / "temp").glob("*.tmp"))

        # 5. Verify other files preserved
        for cat in ['uploads', 'frames', 'contact_sheets', 'outputs']:
            cat_files = list((Path(real_storage) / cat).glob("*.tmp"))
            assert len(cat_files) == 3, f"Expected 3 files in {cat}, got {len(cat_files)}"

    def test_dry_run_simulation(self, manager, real_storage):
        """Test that dry_run truly simulates."""
        # Create temp file
        temp_file = Path(real_storage) / "temp" / "test.tmp"
        temp_file.write_text("test")
        old_time = time.time() - (25 * 3600)
        os.utime(temp_file, (old_time, old_time))

        # Run in dry_run mode
        results = manager.run_cleanup(dry_run=True)

        # File should still exist
        assert temp_file.exists()
        assert results['temp'].files_removed == 0  # Not counted in dry_run

    def test_error_handling(self, manager, real_storage):
        """Test error handling during cleanup."""
        # Create a file and make it read-only
        temp_file = Path(real_storage) / "temp" / "readonly.tmp"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_text("test")
        old_time = time.time() - (25 * 3600)
        os.utime(temp_file, (old_time, old_time))

        # Make read-only
        temp_file.chmod(0o444)

        # Try to delete (should fail gracefully)
        result = manager.cleanup_temp(dry_run=False)

        # Should have logged an error but not crashed
        assert result.category == "temp"
        assert len(result.errors) >= 1  # Error should be recorded

        # Restore permissions for cleanup
        temp_file.chmod(0o644)

    def test_concurrent_cleanup_safety(self, manager, real_storage):
        """Test that concurrent runs don't cause issues."""
        import threading

        # Create many temp files
        for i in range(50):
            temp_file = Path(real_storage) / "temp" / f"test_{i}.tmp"
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file.write_text(f"content {i}")
            old_time = time.time() - (25 * 3600)
            os.utime(temp_file, (old_time, old_time))

        # Run cleanup from multiple threads
        results = []
        errors = []

        def run_cleanup():
            try:
                result = manager.cleanup_temp(dry_run=False)
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=run_cleanup) for _ in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have results (one may win, others may have nothing to clean)
        assert len(errors) == 0  # No crashes
```

#### 5.3 Manual Verification Script

**File**: `/opt/services/media-analysis/bin/verify-storage.sh`

```bash
#!/bin/bash
# /opt/services/media-analysis/bin/verify-storage.sh
# Manual verification script for storage system

set -e

echo "=== Storage System Verification ==="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Activate virtual environment
cd /opt/services/media-analysis
source venv/bin/activate

echo "1. Checking directory structure..."
ERRORS=0
for dir in uploads frames contact-sheets outputs temp; do
    if [ -d "/opt/services/media-analysis/storage/$dir" ]; then
        echo -e "  ${GREEN}✓${NC} /storage/$dir exists"
    else
        echo -e "  ${RED}✗${NC} /storage/$dir missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "2. Testing StorageManager import..."
python3 -c "
from api.storage import StorageManager
print('  StorageManager imported successfully')
" && echo -e "  ${GREEN}✓${NC} Import successful" || echo -e "  ${RED}✗${NC} Import failed"

echo ""
echo "3. Running unit tests..."
pytest /opt/services/media-analysis/tests/test_storage.py -v --tb=short 2>&1 | head -50

echo ""
echo "4. Testing cleanup job (dry run)..."
python3 -c "
from api.scheduler import cleanup_job
result = cleanup_job(dry_run=True)
print(f\"  Status: {result['status']}\")
if result['status'] == 'success':
    print(f\"  Files that would be removed: {result.get('total_files_removed', 0)}\")
    print(f\"  Bytes that would be freed: {result.get('total_bytes_freed', 0)}\")
" && echo -e "  ${GREEN}✓${NC} Cleanup job works" || echo -e "  ${RED}✗${NC} Cleanup job failed"

echo ""
echo "5. Checking API endpoints..."
echo -n "  GET /api/v1/storage/stats: "
curl -s http://localhost:8080/api/v1/storage/stats | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d['file_counts']} files\")" 2>/dev/null || echo "not running"

echo -n "  GET /api/v1/storage/validate: "
curl -s http://localhost:8080/api/v1/storage/validate | python3 -c "import sys,json; d=json.load(sys.stdin); print('valid' if d['valid'] else 'issues')" 2>/dev/null || echo "not running"

echo ""
echo "6. Checking cron fallback..."
if [ -x "/opt/services/media-analysis/bin/cleanup.sh" ]; then
    echo -e "  ${GREEN}✓${NC} Cron script exists and is executable"
else
    echo -e "  ${RED}✗${NC} Cron script missing or not executable"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=== Verification Complete ==="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All checks passed${NC}"
    exit 0
else
    echo -e "${YELLOW}$ERRORS issues found${NC}"
    exit 1
fi
```

#### 5.4 Test Execution Commands

```bash
# Run unit tests
cd /opt/services/media-analysis
source venv/bin/activate
pytest tests/test_storage.py -v

# Run integration tests
pytest tests/test_integration.py -v

# Run all tests
pytest tests/ -v --cov=api.storage

# Generate coverage report
pytest tests/ --cov=api.storage --cov-report=html
open htmlcov/index.html

# Run with pytest-xdist for parallel execution
pytest tests/ -n auto

# Run specific test class
pytest tests/test_storage.py::TestStorageManager -v

# Run single test
pytest tests/test_storage.py::TestStorageManager::test_cleanup_temp_removes_old_files -v
```

#### 5.5 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tests fail in CI/CD | Medium | Medium | Containerized test environment |
| Test data leakage | Low | Medium | Use temp directories, cleanup after |
| Race conditions in tests | Low | Medium | Thread-safe test fixtures |
| Slow test execution | Medium | Medium | Parallel execution with pytest-xdist |
| Flaky tests | Medium | Medium | Proper setup/teardown, retries |

---

## Risk Assessment Summary

### High-Priority Risks

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|------------|
| **Permission errors** | Medium | High | 8/10 | umask handling, error recovery, send2trash |
| **Accidental deletion** | Low | Critical | 9/10 | dry_run mode, send2trash, backup |
| **Disk full scenario** | High | High | 9/10 | Quota enforcement, priority cleanup, monitoring |

### Medium-Priority Risks

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|------------|
| **Scheduler conflicts** | Medium | Medium | 5/10 | max_instances=1, file locking |
| **Large file operations** | Medium | Medium | 5/10 | Batch processing, progress logging |
| **Configuration errors** | Low | High | 6/10 | Validation, defaults, env var overrides |

### Low-Priority Risks

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|------------|
| **Import errors** | Low | Medium | 3/10 | Requirements.txt validation |
| **Performance impact** | Low | Medium | 3/10 | Async scheduling, batch processing |

---

## Rollback Instructions

### Rollback Procedure

**If issues arise after deployment:**

1. **Disable Cleanup Scheduler**
   ```bash
   # Edit config.yaml
   sed -i 's/enabled: true/enabled: false/' /opt/services/media-analysis/config/config.yaml

   # Or set environment variable
   export STORAGE_CLEANUP_ENABLED=false
   ```

2. **Revert to Previous Version**
   ```bash
   # Git revert
   cd /opt/services/media-analysis
   git revert HEAD --no-edit

   # Rebuild and restart
   docker compose build
   docker compose up -d
   ```

3. **Manual Cleanup Recovery**
   ```bash
   # Restore from trash (if send2trash used)
   # Linux: ~/.local/share/Trash/files/
   # Check and restore needed files

   # Or restore from backup
   tar -xzf /backup/media-storage-$(date +%Y%m%d).tar.gz -C /
   ```

4. **Database Rollback** (if applicable)
   ```bash
   # Rollback migration
   alembic downgrade -1
   ```

5. **Restart Services**
   ```bash
   # Docker restart
   docker compose restart

   # Or pod restart (RunPod)
   runpodctl restart pod <pod-id>
   ```

### Emergency Recovery

**If storage fills up completely:**

```bash
# 1. Stop application
docker compose stop

# 2. Emergency cleanup (aggressive)
rm -rf /opt/services/media-analysis/storage/temp/*
rm -rf /opt/services/media-analysis/storage/uploads/*

# 3. Check disk space
df -h /opt/services/media-analysis/storage

# 4. Start application
docker compose start
```

---

## Acceptance Criteria

### Functional Requirements

- [ ] Storage directories created with correct structure
- [ ] TTL-based cleanup works for all categories
- [ ] Quota enforcement prevents disk exhaustion
- [ ] Scheduler runs cleanup daily at 02:00 UTC
- [ ] API endpoints return correct statistics
- [ ] Error handling logs all issues
- [ ] Dry run mode simulates without deleting

### Non-Functional Requirements

- [ ] Cleanup completes in < 5 minutes for 100K files
- [ ] No data loss from bugs (dry_run validation)
- [ ] Scheduler survives app restart
- [ ] Metrics exposed for Prometheus
- [ ] Logs stored in standard location

### Testing Requirements

- [ ] Unit tests pass (100% for core methods)
- [ ] Integration tests pass
- [ ] Manual verification script passes
- [ ] Load testing with 1M files

---

## References

### Related Documents

- `/opt/services/media-analysis/config/config.yaml` - Main configuration
- `/opt/services/media-analysis/api/storage.py` - StorageManager implementation
- `/opt/services/media-analysis/api/scheduler.py` - Scheduler integration
- `/opt/services/media-analysis/tests/test_storage.py` - Unit tests

### External Resources

- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
- [send2trash PyPI](https://pypi.org/project/Send2Trash/)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | Claude | Initial draft |

---

**End of PRD**
