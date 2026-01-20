# Media Analysis API - Storage Organization PRD

**Version**: 1.0
**Date**: 2026-01-20
**Author**: Claude Opus 4.5
**Task**: File Storage Organization System for media-analysis-api
**Context**: Project at /opt/services/media-analysis/

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Implementation Phases](#implementation-phases)
4. [Configuration Schema](#configuration-schema)
5. [Scheduler Integration](#scheduler-integration)
6. [Risk Assessment](#risk-assessment)
7. [Testing & Verification](#testing--verification)

---

## Executive Summary

This PRD defines the implementation of a file storage organization system for the media-analysis-api project. The system will manage storage directories with automated cleanup policies to prevent disk space exhaustion while maintaining data integrity.

**Key Requirements:**
- Storage structure: `/opt/services/media-analysis/storage/{uploads,frames,contact-sheets,outputs,temp}`
- Cleanup policies: temp/ (24h), uploads/ (7d), contact-sheets/ (30d), frames/ (30d), outputs/ (indefinite)
- Integration with existing FastAPI application
- Production-ready with error handling and monitoring

**Deliverables:**
1. Storage directory structure with `.gitkeep` files
2. `StorageManager` class in `/opt/services/media-analysis/api/storage.py`
3. Configuration schema for cleanup policies
4. Scheduler integration for automated cleanup
5. Comprehensive test suite

---

## System Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STORAGE MANAGEMENT MODULE                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     StorageManager Class                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │   │
│  │  │  Cleanup    │  │    File     │  │      Policy Engine          │  │   │
│  │  │  Scheduler  │  │  Operations │  │  (Retention Period Logic)   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Storage Directories                             │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────┐  ┌─────────┐  ┌────────┐ │   │
│  │  │ uploads │  │  frames │  │contact-sheets│ │ outputs │  │  temp  │ │   │
│  │  │  (7d)   │  │  (30d)  │  │   (30d)     │  │   ∞     │  │  (24h) │ │   │
│  │  └─────────┘  └─────────┘  └─────────────┘  └─────────┘  └────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SCHEDULER INTEGRATION                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  APScheduler / FastAPI Lifespan / Cron (Configurable)               │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │                   Cleanup Job                               │    │   │
│  │  │  1. Acquire lock (prevent duplicate runs)                   │    │   │
│  │  │  2. Load configuration                                      │    │   │
│  │  │  3. Scan directories for expired files                      │    │   │
│  │  │  4. Batch delete with error handling                        │    │   │
│  │  │  5. Update metrics                                          │    │   │
│  │  │  6. Release lock                                            │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONFIGURATION                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  config.yaml / Environment Variables                                │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ storage:                                                      │  │   │
│  │  │   base_path: "/opt/services/media-analysis/storage"           │  │   │
│  │  │   retention:                                                  │  │   │
│  │  │     temp: 86400        # 24 hours in seconds                  │  │   │
│  │  │     uploads: 604800     # 7 days in seconds                   │  │   │
│  │  │     contact_sheets: 2592000  # 30 days in seconds             │  │   │
│  │  │     frames: 2592000      # 30 days in seconds                 │  │   │
│  │  │     outputs: -1          # Indefinite (-1)                    │  │   │
│  │  │   cleanup:                                                    │  │   │
│  │  │     enabled: true                                             │  │   │
│  │  │     schedule: "0 2 * * *"    # Daily at 2 AM                  │  │   │
│  │  │     dry_run: false                                           │  │   │
│  │  │     batch_size: 100                                          │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Details

| Component | Purpose | Dependencies |
|-----------|---------|--------------|
| `StorageManager` | Core class for all storage operations | pathlib, os, logging |
| `Policy Engine` | Validates and applies retention rules | config loading |
| `Cleanup scheduler` | Triggers periodic cleanup jobs | APScheduler/FastAPI |
| `File operations` | Safe file deletion with error handling | shutil, pathlib |

---

## Implementation Phases

### PHASE 1: Storage Directory Setup

**Objective**: Create the storage directory structure with proper permissions and git tracking.

#### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `/opt/services/media-analysis/storage/.gitkeep` | Create | Base storage directory marker |
| `/opt/services/media-analysis/storage/uploads/.gitkeep` | Create | Temporary file uploads |
| `/opt/services/media-analysis/storage/frames/.gitkeep` | Create | Extracted video frames |
| `/opt/services/media-analysis/storage/contact-sheets/.gitkeep` | Create | Generated contact sheets |
| `/opt/services/media-analysis/storage/outputs/.gitkeep` | Create | Final output files |
| `/opt/services/media-analysis/storage/temp/.gitkeep` | Create | Temporary processing files |
| `/opt/services/media-analysis/storage/README.md` | Create | Storage usage documentation |
| `/opt/services/media-analysis/api/__init__.py` | Modify | Export StorageManager |

#### Commands

```bash
# Create directory structure
mkdir -p /opt/services/media-analysis/storage/{uploads,frames,contact-sheets,outputs,temp}

# Create .gitkeep files in each directory
for dir in uploads frames contact-sheets outputs temp; do
    touch /opt/services/media-analysis/storage/$dir/.gitkeep
done

# Set permissions (read/write/execute for owner, read/execute for group/others)
chmod 755 /opt/services/media-analysis/storage -R

# Verify structure
tree /opt/services/media-analysis/storage/
```

#### Verification

```bash
# Check directory structure
ls -la /opt/services/media-analysis/storage/
ls -la /opt/services/media-analysis/storage/*/

# Verify .gitkeep files exist
find /opt/services/media-analysis/storage -name ".gitkeep"

# Check permissions
stat -c "%a %n" /opt/services/media-analysis/storage/*/
```

#### Risk Assessment

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Permission denied creating directories | Medium | Low | Run as user with write access to /opt/services |
| Disk space exhausted during creation | High | Low | Verify available space before creation |

---

### PHASE 2: Storage Management Module

**Objective**: Create the `StorageManager` class with all required methods.

#### File: `/opt/services/media-analysis/api/storage.py`

```python
"""
Storage Management Module for media-analysis-api.

Provides StorageManager class for:
- Directory creation and validation
- File cleanup based on retention policies
- Storage statistics and monitoring
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages storage directories and cleanup operations for media-analysis-api.

    Attributes:
        base_path: Root storage directory path
        retention_periods: Dict mapping directory names to retention seconds
        cleanup_config: Configuration for cleanup operations
    """

    # Default retention periods in seconds
    DEFAULT_RETENTION = {
        'temp': 86400,         # 24 hours
        'uploads': 604800,     # 7 days
        'contact_sheets': 2592000,  # 30 days
        'frames': 2592000,     # 30 days
        'outputs': -1,         # Indefinite (never cleanup)
    }

    # Directory names that should exist
    VALID_DIRECTORIES = ['uploads', 'frames', 'contact_sheets', 'outputs', 'temp']

    def __init__(
        self,
        base_path: Optional[str] = None,
        retention_periods: Optional[Dict[str, int]] = None,
        cleanup_config: Optional[Dict] = None
    ):
        """
        Initialize StorageManager.

        Args:
            base_path: Root storage directory (default from config)
            retention_periods: Custom retention periods (seconds)
            cleanup_config: Cleanup scheduler configuration
        """
        self.base_path = Path(base_path or config.STORAGE_BASE_PATH)
        self.retention_periods = retention_periods or self.DEFAULT_RETENTION
        self.cleanup_config = cleanup_config or {}
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate configuration and paths."""
        # Ensure base_path is absolute and within expected location
        if not self.base_path.is_absolute():
            raise ValueError(f"Storage base path must be absolute: {self.base_path}")

        # Validate retention periods
        for directory, period in self.retention_periods.items():
            if not isinstance(period, int):
                raise ValueError(f"Retention period must be integer for {directory}")
            if period < -1:
                raise ValueError(f"Retention period cannot be less than -1 for {directory}")

    def ensure_directories(self) -> Dict[str, bool]:
        """
        Ensure all storage directories exist with correct permissions.

        Returns:
            Dict mapping directory names to existence status
        """
        results = {}
        mode = 0o755  # rwxr-xr-x

        for directory in self.VALID_DIRECTORIES:
            dir_path = self.base_path / directory
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                dir_path.chmod(mode)
                results[directory] = True
                logger.info(f"Ensured directory exists: {dir_path}")
            except PermissionError as e:
                logger.error(f"Permission denied creating {dir_path}: {e}")
                raise
            except OSError as e:
                logger.error(f"OS error creating {dir_path}: {e}")
                raise

        return results

    def _get_file_age_seconds(self, file_path: Path) -> float:
        """
        Get file age in seconds based on modification time.

        Args:
            file_path: Path to file

        Returns:
            Age in seconds (0 for files modified in the future)
        """
        try:
            mtime = file_path.stat().st_mtime
            age = datetime.now().timestamp() - mtime
            return max(0, age)  # Never return negative
        except OSError as e:
            logger.warning(f"Could not stat {file_path}: {e}")
            return 0

    def _should_cleanup(self, file_path: Path, directory: str) -> bool:
        """
        Determine if a file should be cleaned up.

        Args:
            file_path: Path to file
            directory: Parent directory name

        Returns:
            True if file should be deleted
        """
        # Skip .gitkeep files
        if file_path.name == '.gitkeep':
            return False

        # Check if retention is indefinite
        retention = self.retention_periods.get(directory, -1)
        if retention == -1:
            return False

        # Check file age
        age = self._get_file_age_seconds(file_path)
        return age > retention

    def cleanup_directory(
        self,
        directory: str,
        dry_run: bool = False,
        batch_size: int = 100
    ) -> Dict:
        """
        Clean up files in a specific directory based on retention policy.

        Args:
            directory: Directory name (e.g., 'temp', 'uploads')
            dry_run: If True, only report what would be deleted
            batch_size: Number of files to process per batch

        Returns:
            Dict with cleanup results
        """
        results = {
            'directory': directory,
            'dry_run': dry_run,
            'scanned': 0,
            'deleted': 0,
            'failed': 0,
            'space_reclaimed_bytes': 0,
            'errors': [],
            'files': []
        }

        dir_path = self.base_path / directory

        # Validate directory exists
        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {dir_path}")
            return results

        if not dir_path.is_dir():
            logger.error(f"Path is not a directory: {dir_path}")
            return results

        # Collect files to delete
        files_to_delete = []

        try:
            for entry in dir_path.iterdir():
                results['scanned'] += 1

                if entry.is_file() and self._should_cleanup(entry, directory):
                    files_to_delete.append(entry)

        except PermissionError as e:
            results['errors'].append(f"Permission denied scanning {dir_path}: {e}")
            logger.error(f"Permission error scanning {dir_path}: {e}")
            return results

        # Process in batches
        for i in range(0, len(files_to_delete), batch_size):
            batch = files_to_delete[i:i + batch_size]

            for file_path in batch:
                try:
                    if not dry_run:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        results['space_reclaimed_bytes'] += file_size

                    results['deleted'] += 1
                    results['files'].append(str(file_path))

                    logger.info(f"{'Would delete' if dry_run else 'Deleted'}: {file_path}")

                except PermissionError as e:
                    results['failed'] += 1
                    results['errors'].append(f"Permission denied deleting {file_path}: {e}")
                    logger.warning(f"Could not delete {file_path}: {e}")

                except OSError as e:
                    results['failed'] += 1
                    results['errors'].append(f"OS error deleting {file_path}: {e}")
                    logger.error(f"Error deleting {file_path}: {e}")

        # Convert space reclaimed to human-readable
        results['space_reclaimed_human'] = self._format_bytes(
            results['space_reclaimed_bytes']
        )

        return results

    def cleanup_temp(self, dry_run: bool = False) -> Dict:
        """Clean up temporary files (24h retention)."""
        return self.cleanup_directory('temp', dry_run=dry_run)

    def cleanup_uploads(self, dry_run: bool = False) -> Dict:
        """Clean up uploaded files (7d retention)."""
        return self.cleanup_directory('uploads', dry_run=dry_run)

    def cleanup_contact_sheets(self, dry_run: bool = False) -> Dict:
        """Clean up contact sheets (30d retention)."""
        return self.cleanup_directory('contact_sheets', dry_run=dry_run)

    def cleanup_frames(self, dry_run: bool = False) -> Dict:
        """Clean up extracted video frames (30d retention)."""
        return self.cleanup_directory('frames', dry_run=dry_run)

    def cleanup_all(self, dry_run: bool = False) -> Dict:
        """
        Clean up all directories according to their policies.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            Combined cleanup results for all directories
        """
        results = {
            'dry_run': dry_run,
            'total_scanned': 0,
            'total_deleted': 0,
            'total_failed': 0,
            'total_space_reclaimed_bytes': 0,
            'by_directory': {},
            'errors': []
        }

        for directory in self.VALID_DIRECTORIES:
            # Skip outputs (indefinite retention)
            if directory == 'outputs':
                continue

            dir_result = self.cleanup_directory(directory, dry_run=dry_run)
            results['by_directory'][directory] = dir_result

            results['total_scanned'] += dir_result['scanned']
            results['total_deleted'] += dir_result['deleted']
            results['total_failed'] += dir_result['failed']
            results['total_space_reclaimed_bytes'] += dir_result['space_reclaimed_bytes']
            results['errors'].extend(dir_result['errors'])

        results['total_space_reclaimed_human'] = self._format_bytes(
            results['total_space_reclaimed_bytes']
        )

        return results

    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics for all directories.

        Returns:
            Dict with file counts, sizes, and oldest/newest file dates
        """
        stats = {
            'base_path': str(self.base_path),
            'total_size_bytes': 0,
            'total_size_human': '0 B',
            'total_files': 0,
            'total_directories': len(self.VALID_DIRECTORIES),
            'directories': {}
        }

        for directory in self.VALID_DIRECTORIES:
            dir_path = self.base_path / directory

            dir_stats = {
                'path': str(dir_path),
                'files': 0,
                'size_bytes': 0,
                'size_human': '0 B',
                'oldest_file': None,
                'newest_file': None,
                'retention_seconds': self.retention_periods.get(directory, -1),
                'retention_human': self._format_retention(
                    self.retention_periods.get(directory, -1)
                )
            }

            if dir_path.exists() and dir_path.is_dir():
                try:
                    for entry in dir_path.iterdir():
                        if entry.is_file() and entry.name != '.gitkeep':
                            dir_stats['files'] += 1

                            try:
                                file_size = entry.stat().st_size
                                file_mtime = entry.stat().st_mtime

                                dir_stats['size_bytes'] += file_size

                                # Track oldest/newest
                                if dir_stats['oldest_file'] is None:
                                    dir_stats['oldest_file'] = file_mtime
                                    dir_stats['newest_file'] = file_mtime
                                else:
                                    if file_mtime < dir_stats['oldest_file']:
                                        dir_stats['oldest_file'] = file_mtime
                                    if file_mtime > dir_stats['newest_file']:
                                        dir_stats['newest_file'] = file_mtime

                            except OSError:
                                pass  # Skip files we can't stat

                except PermissionError:
                    dir_stats['error'] = 'Permission denied'

            dir_stats['size_human'] = self._format_bytes(dir_stats['size_bytes'])

            if dir_stats['oldest_file']:
                dir_stats['oldest_file'] = datetime.fromtimestamp(
                    dir_stats['oldest_file']
                ).isoformat()
            if dir_stats['newest_file']:
                dir_stats['newest_file'] = datetime.fromtimestamp(
                    dir_stats['newest_file']
                ).isoformat()

            stats['directories'][directory] = dir_stats
            stats['total_size_bytes'] += dir_stats['size_bytes']
            stats['total_files'] += dir_stats['files']

        stats['total_size_human'] = self._format_bytes(stats['total_size_bytes'])

        return stats

    def _format_bytes(self, bytes: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"

    def _format_retention(self, seconds: int) -> str:
        """Format retention period to human-readable string."""
        if seconds == -1:
            return "Indefinite"

        if seconds < 3600:
            return f"{seconds} seconds"
        elif seconds < 86400:
            return f"{seconds // 3600} hours"
        elif seconds < 604800:
            return f"{seconds // 86400} days"
        else:
            return f"{seconds // 86400} days"

    def validate_paths(self) -> Dict[str, Dict]:
        """
        Validate all storage paths are accessible.

        Returns:
            Dict with validation status for each directory
        """
        results = {}

        for directory in self.VALID_DIRECTORIES:
            dir_path = self.base_path / directory

            validation = {
                'path': str(dir_path),
                'exists': dir_path.exists(),
                'is_directory': dir_path.is_dir() if dir_path.exists() else False,
                'readable': os.access(dir_path, os.R_OK) if dir_path.exists() else False,
                'writable': os.access(dir_path, os.W_OK) if dir_path.exists() else False,
            }

            results[directory] = validation

        return results
```

#### Verification

```bash
# Verify file was created
ls -la /opt/services/media-analysis/api/storage.py

# Check Python syntax
python3 -m py_compile /opt/services/media-analysis/api/storage.py

# Run unit tests (Phase 5)
```

#### Risk Assessment

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Memory leak from large directory scans | Medium | Medium | Use batch processing, limit iteration |
| Time zone issues with file modification times | Low | Low | Use UTC timestamps consistently |
| File in use by another process | Low | Medium | Catch OSError, log and continue |

---

### PHASE 3: Configuration Schema

**Objective**: Add storage configuration to the existing config.yaml or create config module integration.

#### Update: `/opt/services/media-analysis/config.yaml`

```yaml
# Storage Configuration
storage:
  # Base path for all storage directories
  base_path: "/opt/services/media-analysis/storage"

  # Retention periods in seconds
  # -1 means indefinite (no cleanup)
  retention:
    temp: 86400              # 24 hours
    uploads: 604800          # 7 days
    contact_sheets: 2592000  # 30 days
    frames: 2592000          # 30 days
    outputs: -1              # Indefinite

  # Cleanup scheduler configuration
  cleanup:
    enabled: true
    schedule: "0 2 * * *"    # Cron format: daily at 2:00 AM
    dry_run: false           # When true, only simulate cleanup
    batch_size: 100          # Files per batch for memory safety
    lock_timeout: 300        # Lock file timeout in seconds (5 min)
```

#### Alternative: Environment Variables

```bash
# Environment variable overrides
export STORAGE_BASE_PATH="/opt/services/media-analysis/storage"
export STORAGE_RETENTION_TEMP=86400
export STORAGE_RETENTION_UPLOADS=604800
export STORAGE_RETENTION_CONTACT_SHEETS=2592000
export STORAGE_RETENTION_FRAMES=2592000
export STORAGE_RETENTION_OUTPUTS=-1
export STORAGE_CLEANUP_ENABLED=true
export STORAGE_CLEANUP_SCHEDULE="0 2 * * *"
export STORAGE_CLEANUP_DRY_RUN=false
export STORAGE_CLEANUP_BATCH_SIZE=100
```

#### Update: `/opt/services/media-analysis/api/config.py`

```python
# Add to existing config module
import os
from pathlib import Path
from typing import Dict, Any
import yaml


class Config:
    """Configuration management for media-analysis-api."""

    # Default storage configuration
    STORAGE_DEFAULTS = {
        'base_path': '/opt/services/media-analysis/storage',
        'retention': {
            'temp': 86400,
            'uploads': 604800,
            'contact_sheets': 2592000,
            'frames': 2592000,
            'outputs': -1,
        },
        'cleanup': {
            'enabled': True,
            'schedule': '0 2 * * *',
            'dry_run': False,
            'batch_size': 100,
            'lock_timeout': 300,
        }
    }

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._find_config()
        self._config = self._load_config()

    def _find_config(self) -> str:
        """Find config.yaml in standard locations."""
        search_paths = [
            Path(__file__).parent.parent / 'config.yaml',
            Path.cwd() / 'config.yaml',
            Path('/opt/services/media-analysis/config.yaml'),
        ]

        for path in search_paths:
            if path.exists():
                return str(path)

        return str(search_paths[0])

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config = self.STORAGE_DEFAULTS.copy()

        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                file_config = yaml.safe_load(f) or {}

                # Merge storage configuration
                if 'storage' in file_config:
                    config.update(file_config['storage'])

        # Apply environment variable overrides
        config = self._apply_env_overrides(config)

        return config

    def _apply_env_overrides(self, config: Dict) -> Dict:
        """Apply environment variable overrides to configuration."""
        # Base path
        if os.getenv('STORAGE_BASE_PATH'):
            config['base_path'] = os.getenv('STORAGE_BASE_PATH')

        # Retention periods
        retention_keys = ['temp', 'uploads', 'contact_sheets', 'frames', 'outputs']
        for key in retention_keys:
            env_key = f'STORAGE_RETENTION_{key.upper()}'
            if os.getenv(env_key):
                config['retention'][key] = int(os.getenv(env_key))

        # Cleanup settings
        if os.getenv('STORAGE_CLEANUP_ENABLED'):
            config['cleanup']['enabled'] = os.getenv('STORAGE_CLEANUP_ENABLED').lower() == 'true'
        if os.getenv('STORAGE_CLEANUP_SCHEDULE'):
            config['cleanup']['schedule'] = os.getenv('STORAGE_CLEANUP_SCHEDULE')
        if os.getenv('STORAGE_CLEANUP_DRY_RUN'):
            config['cleanup']['dry_run'] = os.getenv('STORAGE_CLEANUP_DRY_RUN').lower() == 'true'
        if os.getenv('STORAGE_CLEANUP_BATCH_SIZE'):
            config['cleanup']['batch_size'] = int(os.getenv('STORAGE_CLEANUP_BATCH_SIZE'))

        return config

    @property
    def storage_base_path(self) -> str:
        return self._config.get('base_path', self.STORAGE_DEFAULTS['base_path'])

    @property
    def storage_retention(self) -> Dict[str, int]:
        return self._config.get('retention', self.STORAGE_DEFAULTS['retention'])

    @property
    def storage_cleanup(self) -> Dict:
        return self._config.get('cleanup', self.STORAGE_DEFAULTS['cleanup'])

    @property
    def STORAGE_BASE_PATH(self) -> str:
        """Legacy property for backward compatibility."""
        return self.storage_base_path


# Global config instance
config = Config()
```

#### Verification

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('/opt/services/media-analysis/config.yaml'))"
echo "YAML syntax OK"

# Test config loading
cd /opt/services/media-analysis
python3 -c "from api.config import Config; c = Config(); print(c.storage_base_path)"
```

#### Risk Assessment

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Invalid YAML syntax | Medium | Low | Validate before deployment |
| Missing environment variables | Low | Low | Provide defaults for all config |
| Path permissions | Medium | Low | Validate paths at startup |

---

### PHASE 4: Scheduler Integration

**Objective**: Integrate cleanup scheduler with existing application infrastructure.

#### Option A: APScheduler Integration (Recommended)

**File**: `/opt/services/media-analysis/api/scheduler.py`

```python
"""
Background scheduler for media-analysis-api.

Provides APScheduler integration for automated cleanup operations.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .storage import StorageManager
from .config import Config

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """
    Scheduler for automated storage cleanup operations.

    Features:
    - Cron-based scheduling
    - Lock file to prevent duplicate runs
    - Error handling and logging
    - Metrics collection
    """

    LOCK_FILE = '/tmp/media-analysis-cleanup.lock'

    def __init__(self, config: Config = None, storage_manager: StorageManager = None):
        """
        Initialize cleanup scheduler.

        Args:
            config: Configuration instance
            storage_manager: StorageManager instance
        """
        self.config = config or Config()
        self.storage_manager = storage_manager or StorageManager(
            base_path=self.config.storage_base_path,
            retention_periods=self.config.storage_retention,
            cleanup_config=self.config.storage_cleanup
        )
        self.scheduler = None
        self._metrics = {
            'last_run': None,
            'last_success': None,
            'total_runs': 0,
            'total_deleted': 0,
            'total_space_reclaimed_bytes': 0,
        }

    def _acquire_lock(self) -> bool:
        """Acquire lock file to prevent duplicate cleanup runs."""
        try:
            # Check if lock file exists and is fresh
            if Path(self.LOCK_FILE).exists():
                lock_mtime = Path(self.LOCK_FILE).stat().st_mtime
                lock_age = datetime.now().timestamp() - lock_mtime

                timeout = self.config.storage_cleanup.get('lock_timeout', 300)
                if lock_age > timeout:
                    # Lock expired, remove it
                    Path(self.LOCK_FILE).unlink()
                else:
                    logger.info(f"Cleanup already running (lock file exists)")
                    return False

            # Create lock file
            Path(self.LOCK_FILE).touch()
            return True

        except PermissionError:
            logger.warning("Could not create lock file (permission denied)")
            return False

    def _release_lock(self) -> None:
        """Release lock file after cleanup completes."""
        try:
            if Path(self.LOCK_FILE).exists():
                Path(self.LOCK_FILE).unlink()
        except PermissionError:
            logger.warning("Could not remove lock file (permission denied)")

    def _cleanup_job(self) -> None:
        """Execute cleanup job with error handling."""
        if not self._acquire_lock():
            return

        self._metrics['total_runs'] += 1
        self._metrics['last_run'] = datetime.now().isoformat()

        try:
            # Check if cleanup is enabled
            if not self.config.storage_cleanup.get('enabled', True):
                logger.info("Cleanup is disabled in configuration")
                return

            dry_run = self.config.storage_cleanup.get('dry_run', False)
            batch_size = self.config.storage_cleanup.get('batch_size', 100)

            logger.info(f"Starting cleanup job (dry_run={dry_run})")

            # Run cleanup
            result = self.storage_manager.cleanup_all(dry_run=dry_run)

            # Update metrics
            self._metrics['total_deleted'] += result['total_deleted']
            self._metrics['total_space_reclaimed_bytes'] += result['total_space_reclaimed_bytes']
            self._metrics['last_success'] = datetime.now().isoformat()

            # Log summary
            logger.info(
                f"Cleanup completed: {result['total_deleted']} files deleted, "
                f"{result['total_space_reclaimed_human']} reclaimed"
            )

            # Log per-directory results
            for directory, dir_result in result['by_directory'].items():
                if dir_result['deleted'] > 0:
                    logger.info(
                        f"  {directory}: {dir_result['deleted']} files, "
                        f"{dir_result['space_reclaimed_human']}"
                    )

            if result['errors']:
                logger.warning(f"Cleanup had {len(result['errors'])} errors")
                for error in result['errors'][:5]:  # Log first 5 errors
                    logger.warning(f"  {error}")

        except Exception as e:
            logger.error(f"Cleanup job failed: {e}", exc_info=True)
            raise

        finally:
            self._release_lock()

    def _job_listener(self, event) -> None:
        """Listen for job events."""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            logger.debug(f"Job {event.job_id} executed successfully")

    def start(self) -> None:
        """Start the background scheduler."""
        if self.scheduler is not None:
            logger.warning("Scheduler already running")
            return

        self.scheduler = BackgroundScheduler()

        # Parse cron schedule
        schedule = self.config.storage_cleanup.get('schedule', '0 2 * * *')

        try:
            trigger = CronTrigger.from_crontab(schedule)
            self.scheduler.add_job(
                self._cleanup_job,
                trigger=trigger,
                id='storage_cleanup',
                name='Storage Cleanup',
                replace_existing=True,
                max_instances=1,  # Prevent overlapping runs
            )

            # Add event listener
            self.scheduler.add_listener(
                self._job_listener,
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
            )

            self.scheduler.start()
            logger.info(f"Cleanup scheduler started with schedule: {schedule}")

        except ValueError as e:
            logger.error(f"Invalid cron schedule '{schedule}': {e}")
            raise

    def stop(self) -> None:
        """Stop the background scheduler."""
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            logger.info("Cleanup scheduler stopped")

    def run_now(self) -> Dict:
        """Manually trigger cleanup (for testing/admin use)."""
        if self.scheduler and self.scheduler.running:
            # Run in current thread
            self._cleanup_job()
        else:
            # Run directly
            self._cleanup_job()

        return self.get_metrics()

    def get_metrics(self) -> Dict:
        """Get scheduler metrics."""
        return {
            'schedule': self.config.storage_cleanup.get('schedule', '0 2 * * *'),
            'enabled': self.config.storage_cleanup.get('enabled', True),
            'last_run': self._metrics['last_run'],
            'last_success': self._metrics['last_success'],
            'total_runs': self._metrics['total_runs'],
            'total_deleted': self._metrics['total_deleted'],
            'total_space_reclaimed_bytes': self._metrics['total_space_reclaimed_bytes'],
            'total_space_reclaimed_human': self._format_bytes(
                self._metrics['total_space_reclaimed_bytes']
            ),
            'running': self.scheduler.running if self.scheduler else False,
        }

    def _format_bytes(self, bytes: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"


# Global scheduler instance
cleanup_scheduler = None


def get_scheduler() -> CleanupScheduler:
    """Get or create the global scheduler instance."""
    global cleanup_scheduler
    if cleanup_scheduler is None:
        cleanup_scheduler = CleanupScheduler()
    return cleanup_scheduler
```

#### FastAPI Integration

**File**: `/opt/services/media-analysis/api/main.py` (or lifespan.py)

```python
"""
FastAPI application with storage cleanup scheduler integration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import Config
from .scheduler import CleanupScheduler, get_scheduler
from .storage import StorageManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown of background services.
    """
    config = Config()

    # Ensure storage directories exist
    storage_manager = StorageManager(
        base_path=config.storage_base_path,
        retention_periods=config.storage_retention,
        cleanup_config=config.storage_cleanup
    )
    storage_manager.ensure_directories()

    # Start cleanup scheduler
    scheduler = CleanupScheduler(config=config, storage_manager=storage_manager)

    if config.storage_cleanup.get('enabled', True):
        scheduler.start()

    yield

    # Shutdown
    scheduler.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/storage/stats")
async def get_storage_stats():
    """Get storage statistics."""
    scheduler = get_scheduler()
    storage_manager = scheduler.storage_manager
    return storage_manager.get_storage_stats()


@app.get("/storage/cleanup")
async def trigger_cleanup(dry_run: bool = False):
    """Manually trigger storage cleanup."""
    scheduler = get_scheduler()
    return scheduler.run_now()


@app.get("/storage/metrics")
async def get_storage_metrics():
    """Get cleanup scheduler metrics."""
    scheduler = get_scheduler()
    return scheduler.get_metrics()
```

#### Option B: System Cron (Alternative)

```bash
# /etc/cron.d/media-analysis-cleanup
# Run cleanup daily at 2:00 AM

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

0 2 * * * root cd /opt/services/media-analysis && python3 -c "
from api.storage import StorageManager
from api.config import Config
c = Config()
s = StorageManager(base_path=c.storage_base_path, retention_periods=c.storage_retention)
s.cleanup_all()
" >> /var/log/media-analysis-cleanup.log 2>&1
```

#### Verification

```bash
# Test scheduler initialization
cd /opt/services/media-analysis
python3 -c "
from api.scheduler import CleanupScheduler
from api.config import Config
c = Config()
s = CleanupScheduler(config=c)
print('Scheduler initialized successfully')
print(f'Schedule: {c.storage_cleanup.get(\"schedule\")}')
"

# Test cron syntax validation
echo "0 2 * * *" | python3 -c "
import sys
import re
cron = sys.stdin.read().strip()
parts = cron.split()
if len(parts) != 5:
    print('Invalid cron format')
    sys.exit(1)
print('Cron format valid')
"
```

#### Risk Assessment

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Scheduler not starting on app crash | Medium | Low | Use cron as backup |
| Duplicate cleanup runs | Medium | Low | Lock file mechanism |
| Scheduler blocking app shutdown | Low | Medium | Proper shutdown in lifespan |
| Memory leak from long-running scheduler | Low | Low | APScheduler is well-tested |

---

### PHASE 5: Testing & Verification

**Objective**: Comprehensive test suite and manual verification.

#### Unit Tests: `/opt/services/media-analysis/tests/test_storage.py`

```python
"""
Unit tests for StorageManager.
"""

import os
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.storage import StorageManager


class TestStorageManager:
    """Test cases for StorageManager class."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / 'storage'
            storage_path.mkdir()

            # Create subdirectories
            for subdir in ['uploads', 'frames', 'contact_sheets', 'outputs', 'temp']:
                (storage_path / subdir).mkdir()
                (storage_path / subdir / '.gitkeep').touch()

            yield storage_path

    @pytest.fixture
    def storage_manager(self, temp_storage):
        """Create StorageManager instance for testing."""
        return StorageManager(
            base_path=str(temp_storage),
            retention_periods={
                'temp': 1,           # 1 second (immediate cleanup)
                'uploads': 3600,     # 1 hour
                'contact_sheets': 86400,  # 1 day
                'frames': 86400,     # 1 day
                'outputs': -1,       # Indefinite
            }
        )

    def test_ensure_directories(self, temp_storage, storage_manager):
        """Test directory creation."""
        result = storage_manager.ensure_directories()

        for directory in storage_manager.VALID_DIRECTORIES:
            assert result[directory] is True
            assert (temp_storage / directory).exists()
            assert (temp_storage / directory).is_dir()

    def test_get_file_age_seconds(self, temp_storage):
        """Test file age calculation."""
        manager = StorageManager(base_path=str(temp_storage))

        # Create test file
        test_file = temp_storage / 'test.txt'
        test_file.write_text('test')

        age = manager._get_file_age_seconds(test_file)
        assert age >= 0
        assert age < 10  # Should be very recent

    def test_should_cleanup_temp_files(self, temp_storage):
        """Test cleanup decision for temporary files."""
        manager = StorageManager(
            base_path=str(temp_storage),
            retention_periods={'temp': 1, 'uploads': 3600}
        )

        # Create old temp file
        old_file = temp_storage / 'temp' / 'old.tmp'
        old_file.write_text('old')
        old_time = datetime.now() - timedelta(seconds=2)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        # Create recent temp file
        recent_file = temp_storage / 'temp' / 'recent.tmp'
        recent_file.write_text('recent')

        # Old file should be flagged for cleanup
        assert manager._should_cleanup(old_file, 'temp') is True

        # Recent file should not
        assert manager._should_cleanup(recent_file, 'temp') is False

    def test_should_not_cleanup_outputs(self, temp_storage):
        """Test that outputs directory is never cleaned up."""
        manager = StorageManager(
            base_path=str(temp_storage),
            retention_periods={'outputs': -1}
        )

        # Create old output file
        old_output = temp_storage / 'outputs' / 'old.out'
        old_output.write_text('old')
        old_time = datetime.now() - timedelta(days=100)
        os.utime(old_output, (old_time.timestamp(), old_time.timestamp()))

        # Should NOT be flagged for cleanup (indefinite retention)
        assert manager._should_cleanup(old_output, 'outputs') is False

    def test_cleanup_directory_dry_run(self, temp_storage, storage_manager):
        """Test cleanup in dry run mode."""
        # Create test files
        old_file = temp_storage / 'temp' / 'old.tmp'
        old_file.write_text('old')
        old_time = datetime.now() - timedelta(seconds=2)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        result = storage_manager.cleanup_directory('temp', dry_run=True)

        assert result['dry_run'] is True
        assert result['scanned'] >= 1
        assert result['deleted'] == 0  # Not actually deleted
        assert result['space_reclaimed_bytes'] == 0

    def test_cleanup_directory_actual_delete(self, temp_storage):
        """Test actual file deletion."""
        manager = StorageManager(
            base_path=str(temp_storage),
            retention_periods={'temp': 1}
        )

        # Create test file
        test_file = temp_storage / 'temp' / 'test.tmp'
        test_file.write_text('test')
        old_time = datetime.now() - timedelta(seconds=2)
        os.utime(test_file, (old_time.timestamp(), old_time.timestamp()))

        assert test_file.exists()

        result = manager.cleanup_directory('temp', dry_run=False)

        assert result['deleted'] >= 1
        assert test_file.exists() is False

    def test_cleanup_all_directories(self, temp_storage, storage_manager):
        """Test cleanup of all directories."""
        # Create test files in multiple directories
        for directory in ['uploads', 'frames', 'contact_sheets']:
            old_file = temp_storage / directory / 'old.file'
            old_file.write_text('old')
            old_time = datetime.now() - timedelta(hours=2)
            os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        result = storage_manager.cleanup_all(dry_run=False)

        assert result['total_deleted'] >= 3
        assert result['total_scanned'] >= 3
        assert 'uploads' in result['by_directory']
        assert 'frames' in result['by_directory']

    def test_get_storage_stats(self, temp_storage, storage_manager):
        """Test storage statistics."""
        # Create test files
        (temp_storage / 'uploads' / 'test1.txt').write_text('test1')
        (temp_storage / 'uploads' / 'test2.txt').write_text('test2' * 1000)

        stats = storage_manager.get_storage_stats()

        assert stats['total_size_bytes'] > 0
        assert stats['total_files'] >= 2
        assert 'uploads' in stats['directories']
        assert stats['directories']['uploads']['files'] >= 2

    def test_validate_paths(self, temp_storage, storage_manager):
        """Test path validation."""
        results = storage_manager.validate_paths()

        for directory in storage_manager.VALID_DIRECTORIES:
            assert results[directory]['exists'] is True
            assert results[directory]['is_directory'] is True
            assert results[directory]['readable'] is True
            assert results[directory]['writable'] is True

    def test_format_bytes(self, storage_manager):
        """Test byte formatting."""
        assert storage_manager._format_bytes(500) == "500.00 B"
        assert storage_manager._format_bytes(2048) == "2.00 KB"
        assert storage_manager._format_bytes(1048576) == "1.00 MB"
        assert storage_manager._format_bytes(1073741824) == "1.00 GB"

    def test_format_retention(self, storage_manager):
        """Test retention period formatting."""
        assert storage_manager._format_retention(-1) == "Indefinite"
        assert storage_manager._format_retention(3600) == "1 hours"
        assert storage_manager._format_retention(86400) == "1 days"
        assert storage_manager._format_retention(604800) == "7 days"

    def test_skip_gitkeep_files(self, temp_storage, storage_manager):
        """Test that .gitkeep files are not deleted."""
        gitkeep = temp_storage / 'uploads' / '.gitkeep'
        assert gitkeep.exists()

        result = storage_manager.cleanup_directory('uploads', dry_run=False)

        assert gitkeep.exists()  # .gitkeep should still exist
        # Only count actual files, not .gitkeep
        if result['scanned'] > 0:
            assert '.gitkeep' not in str(result.get('files', []))
```

#### Integration Tests: `/opt/services/media-analysis/tests/test_integration.py`

```python
"""
Integration tests for storage cleanup with scheduler.
"""

import pytest
from pathlib import Path
import tempfile
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.storage import StorageManager
from api.scheduler import CleanupScheduler
from api.config import Config


class TestSchedulerIntegration:
    """Integration tests for scheduler integration."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("""
storage:
  base_path: "{tmpdir}/storage"
  retention:
    temp: 1
    uploads: 3600
    contact_sheets: 86400
    frames: 86400
    outputs: -1
  cleanup:
    enabled: true
    schedule: "0 2 * * *"
    dry_run: false
    batch_size: 10
""".format(tmpdir=tmpdir))

            # Create storage directories
            storage_path = Path(tmpdir) / 'storage'
            storage_path.mkdir()
            for subdir in ['uploads', 'frames', 'contact_sheets', 'outputs', 'temp']:
                (storage_path / subdir).mkdir()

            yield config_path

    def test_scheduler_initialization(self, temp_config):
        """Test scheduler can be initialized."""
        from api.config import Config

        config = Config(str(temp_config))
        scheduler = CleanupScheduler(config=config)

        assert scheduler is not None
        assert scheduler.scheduler is None  # Not started yet

    def test_scheduler_run_now(self, temp_config):
        """Test manual trigger of cleanup job."""
        from api.config import Config

        config = Config(str(temp_config))
        scheduler = CleanupScheduler(config=config)

        # Create test files
        storage_path = Path(config.storage_base_path)
        old_file = storage_path / 'temp' / 'test.tmp'
        old_file.write_text('test')

        # Trigger cleanup
        result = scheduler.run_now()

        assert result['total_runs'] == 1
        assert old_file.exists() is False

    def test_scheduler_metrics(self, temp_config):
        """Test metrics collection."""
        from api.config import Config

        config = Config(str(temp_config))
        scheduler = CleanupScheduler(config=config)

        metrics = scheduler.get_metrics()

        assert 'schedule' in metrics
        assert 'enabled' in metrics
        assert 'total_runs' in metrics
        assert 'total_deleted' in metrics
```

#### Manual Verification Script

**File**: `/opt/services/media-analysis/verify_storage.py`

```python
#!/usr/bin/env python3
"""
Manual verification script for storage management system.

Usage: python3 verify_storage.py [--dry-run]
"""

import sys
import argparse
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from api.storage import StorageManager
from api.scheduler import CleanupScheduler
from api.config import Config


def verify_directories(storage_manager):
    """Verify all storage directories exist and are accessible."""
    print("\n=== Directory Verification ===")
    validation = storage_manager.validate_paths()

    all_valid = True
    for directory, status in validation.items():
        icon = "✓" if status['exists'] and status['writable'] else "✗"
        print(f"  {icon} {directory}: {status['path']}")
        print(f"      exists={status['exists']}, writable={status['writable']}")

        if not status['exists'] or not status['writable']:
            all_valid = False

    return all_valid


def verify_stats(storage_manager):
    """Display storage statistics."""
    print("\n=== Storage Statistics ===")
    stats = storage_manager.get_storage_stats()

    print(f"  Base path: {stats['base_path']}")
    print(f"  Total size: {stats['total_size_human']}")
    print(f"  Total files: {stats['total_files']}")

    for directory, dir_stats in stats['directories'].items():
        print(f"\n  {directory}:")
        print(f"    Files: {dir_stats['files']}")
        print(f"    Size: {dir_stats['size_human']}")
        print(f"    Retention: {dir_stats['retention_human']}")
        if dir_stats['oldest_file']:
            print(f"    Oldest: {dir_stats['oldest_file']}")
        if dir_stats['newest_file']:
            print(f"    Newest: {dir_stats['newest_file']}")

    return True


def test_cleanup(storage_manager, dry_run=False):
    """Test cleanup operation."""
    print(f"\n=== Cleanup Test (dry_run={dry_run}) ===")

    result = storage_manager.cleanup_all(dry_run=dry_run)

    print(f"  Scanned: {result['total_scanned']}")
    print(f"  Deleted: {result['total_deleted']}")
    print(f"  Failed: {result['total_failed']}")
    print(f"  Space reclaimed: {result['total_space_reclaimed_human']}")

    if result['errors']:
        print(f"  Errors: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"    - {error}")

    return result['total_failed'] == 0


def test_scheduler(config):
    """Test scheduler functionality."""
    print("\n=== Scheduler Test ===")

    scheduler = CleanupScheduler(config=config)

    # Check configuration
    print(f"  Schedule: {config.storage_cleanup.get('schedule')}")
    print(f"  Enabled: {config.storage_cleanup.get('enabled')}")
    print(f"  Dry run: {config.storage_cleanup.get('dry_run')}")

    # Run cleanup manually
    result = scheduler.run_now()
    print(f"  Last run: {result['last_run']}")
    print(f"  Total runs: {result['total_runs']}")
    print(f"  Total deleted: {result['total_deleted']}")

    return True


def main():
    parser = argparse.ArgumentParser(description='Verify storage management system')
    parser.add_argument('--dry-run', action='store_true', help='Run cleanup in dry-run mode')
    parser.add_argument('--skip-cleanup', action='store_true', skip cleanup test')
    parser.add_argument('--skip-scheduler', action='store_true', skip scheduler test')
    args = parser.parse_args()

    print("=" * 50)
    print("Storage Management System Verification")
    print("=" * 50)

    # Load configuration
    try:
        config = Config()
        print(f"Config loaded: {config.config_path}")
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Create storage manager
    try:
        storage_manager = StorageManager(
            base_path=config.storage_base_path,
            retention_periods=config.storage_retention,
            cleanup_config=config.storage_cleanup
        )
        print(f"Storage manager initialized: {storage_manager.base_path}")
    except Exception as e:
        print(f"Error initializing storage manager: {e}")
        sys.exit(1)

    # Run verification tests
    results = []

    # 1. Verify directories
    results.append(("Directories", verify_directories(storage_manager)))

    # 2. Verify stats
    results.append(("Statistics", verify_stats(storage_manager)))

    # 3. Test cleanup
    if not args.skip_cleanup:
        results.append(("Cleanup", test_cleanup(storage_manager, dry_run=args.dry_run)))

    # 4. Test scheduler
    if not args.skip_scheduler:
        results.append(("Scheduler", test_scheduler(config)))

    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        icon = "✓" if passed else "✗"
        print(f"  {icon} {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll checks passed!")
        sys.exit(0)
    else:
        print("\nSome checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

#### Test Execution

```bash
cd /opt/services/media-analysis

# Install test dependencies
pip install pytest pytest-asyncio

# Run unit tests
python3 -m pytest tests/test_storage.py -v

# Run integration tests
python3 -m pytest tests/test_integration.py -v

# Run all tests
python3 -m pytest tests/ -v --tb=short

# Run verification script
python3 verify_storage.py --dry-run
python3 verify_storage.py  # Actual cleanup
```

#### Risk Assessment

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Tests not covering edge cases | Medium | Medium | Add integration tests for error scenarios |
| Verification script failing | Low | Low | Fix before deployment |
| Cleanup timing issues in tests | Low | Medium | Use time.freeze or mock datetime |

---

## Risk Assessment Summary

| Risk | Severity | Probability | Mitigation | Contingency |
|------|----------|-------------|------------|-------------|
| Permission errors during cleanup | Medium | Low | umask handling, error recovery | Log errors, skip problematic files |
| Large file operations timeout | Medium | Medium | Batch processing, progress logging | Increase timeout, add retry logic |
| Accidental deletion of valid files | High | Low | dry_run mode, backup before cleanup | Restore from backup, add safety checks |
| Scheduler conflicts (duplicate runs) | Medium | Low | Lock mechanism, idempotent operations | Kill stale processes, manual intervention |
| Disk full during cleanup | Medium | Low | Priority-based cleanup, alerts | Emergency cleanup, notify admin |
| Files in use by other processes | Low | Medium | Catch OSError, log and continue | Retry with delay, skip locked files |
| Time zone issues | Low | Low | UTC timestamps consistently | Use datetime.now().timestamp() |
| Path validation failures | Low | Low | Startup validation, error messages | Fix paths before deployment |

---

## Rollback Instructions

If deployment causes issues:

```bash
# 1. Stop the application
cd /opt/services/media-analysis
docker compose down  # or systemctl stop media-analysis

# 2. Restore previous storage.py
git checkout HEAD -- api/storage.py

# 3. Remove new storage directories (if safe)
rm -rf /opt/services/media-analysis/storage/

# 4. Restore config if modified
git checkout HEAD -- config.yaml

# 5. Restart application
docker compose up -d
```

---

## DO NOT MODIFY

- `/opt/services/media-analysis/existing_api.py` - Unrelated to storage management
- `/opt/services/media-analysis/database/` - Separate module with own cleanup
- `/opt/services/media-analysis/tests/conftest.py` - May conflict with test fixtures

---

## References

- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html)
- [APScheduler documentation](https://apscheduler.readthedocs.io/)
- [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [YAML configuration best practices](https://yaml.org/)
- [File permissions in Linux](https://www.gnu.org/software/coreutils/manual/html_node/File-permissions.html)
