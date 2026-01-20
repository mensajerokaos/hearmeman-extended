---
task: Research storage organization patterns and cleanup libraries for media-analysis-api
agent: hc (Claude Sonnet 4.5 fallback)
model: claude-sonnet-4-5-20250929
timestamp: 2026-01-20T05:32:00Z
status: completed
author: $USER
---

# Storage Organization & Cleanup Research Findings

## 1. Storage Organization Patterns

### Pattern 1: Time-Based TTL (Time-To-Live)
The most common pattern for media processing pipelines involves categorizing storage by processing stage and applying time-based retention policies.

**Recommended Structure**:
```
storage/
├── uploads/      (24h-7d TTL)    - Raw user uploads
├── frames/       (7-30d TTL)     - Extracted video frames
├── contact-sheets/ (30d TTL)     - Generated thumbnails/previews
├── outputs/      (indefinite)    - Final processed outputs
└── temp/         (24h TTL)       - Temporary processing files
```

**Rationale**:
- `uploads/`: Short TTL prevents accumulation of unprocessed media
- `frames/`: Medium TTL for debugging and reprocessing
- `contact-sheets/`: Medium TTL for reference purposes
- `outputs/`: Indefinite as these are primary deliverables
- `temp/`: Very short TTL as these are intermediate files

### Pattern 2: Hierarchical Storage Organization
For large-scale deployments, implement tiered storage:

| Tier | Storage Type | Example | TTL |
|------|--------------|---------|-----|
| Hot | SSD/NVMe | temp/, uploads/ | 24h-7d |
| Warm | HDD | frames/, contact-sheets/ | 7-30d |
| Cold | Object Storage (S3/R2) | outputs/ | Indefinite |

### Pattern 3: Quota-Based Cleanup
Implement storage quotas per directory to prevent disk exhaustion:

```python
STORAGE_QUOTAS = {
    'uploads': 10 * 1024**3,      # 10GB
    'frames': 50 * 1024**3,       # 50GB
    'contact-sheets': 20 * 1024**3, # 20GB
    'outputs': 100 * 1024**3,     # 100GB
    'temp': 5 * 1024**3,          # 5GB
}
```

---

## 2. Python File Cleanup Libraries

### 2.1 Standard Library: `pathlib` (Python 3.4+)

**Advantages**:
- Modern, object-oriented path manipulation
- Built-in methods for file operations
- No external dependencies
- Platform-independent path handling

**Key Methods**:
```python
from pathlib import Path
import time

# File age calculation
file_path = Path("/opt/services/media-analysis/storage/temp/test.jpg")
age_seconds = time.time() - file_path.stat().st_mtime

# Recursive directory listing
temp_dir = Path("/opt/services/media-analysis/storage/temp")
old_files = [f for f in temp_dir.rglob("*")
             if f.is_file() and
             (time.time() - f.stat().st_mtime) > 86400]

# Safe deletion (check exists first)
if file_path.exists() and file_path.is_file():
    file_path.unlink()
```

**Best For**: Simple cleanup operations, modern Python codebases

### 2.2 Standard Library: `shutil` (Python 2.3+)

**Advantages**:
- High-level file operations
- Recursive directory removal
- File copying and archiving

**Key Methods**:
```python
import shutil
import os
from datetime import datetime, timedelta

def cleanup_old_files(directory, max_age_seconds):
    """Remove files older than max_age_seconds."""
    cutoff = datetime.now() - timedelta(seconds=max_age_seconds)

    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

            if mtime < cutoff:
                try:
                    os.remove(filepath)
                    print(f"Removed: {filepath}")
                except OSError as e:
                    print(f"Error removing {filepath}: {e}")

# Recursive cleanup with error handling
def cleanup_directory_tree(path, ignore_errors=False):
    """Remove directory tree safely."""
    try:
        shutil.rmtree(path, ignore_errors=ignore_errors)
    except OSError as e:
        print(f"Error removing {path}: {e}")
```

**Best For**: Recursive operations, cross-platform compatibility

### 2.3 Third-Party: `send2trash`

**Advantages**:
- Moves files to OS trash instead of permanent deletion
- Safer for production environments
- Reversible operations
- Cross-platform support (Windows, macOS, Linux)

**Installation**:
```bash
pip install send2trash
```

**Usage**:
```python
from send2trash import send2trash
import glob

# Safe delete to trash
old_files = glob.glob("/opt/services/media-analysis/storage/temp/*")
for filepath in old_files:
    try:
        send2trash(filepath)
        print(f"Moved to trash: {filepath}")
    except Exception as e:
        print(f"Error: {e}")

# Batch operations
import os
from send2trash import send2trash

def batch_trash(pattern, max_files=100):
    """Trash files matching pattern, max N files."""
    files = sorted(glob.glob(pattern))[:max_files]
    for f in files:
        send2trash(f)
    return len(files)
```

**Best For**: Production systems where accidental deletion is costly

### 2.4 Third-Party: ` APScheduler`

**Advantages**:
- In-process job scheduler
- Multiple backend options (memory, Redis, MongoDB)
- Cron-style scheduling
- Persistent job stores

**Installation**:
```bash
pip install apscheduler
```

**Usage**:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

def cleanup_job():
    """Daily cleanup job at 02:00 UTC."""
    from api.storage import StorageManager
    manager = StorageManager()
    result = manager.run_cleanup()
    return result

scheduler = BackgroundScheduler()
scheduler.add_job(
    cleanup_job,
    trigger=CronTrigger(hour=2, minute=0),
    id='storage_cleanup',
    name='Daily storage cleanup',
    replace_existing=True
)
scheduler.start()
```

**Best For**: Application-integrated scheduling, no external cron dependency

### 2.5 Third-Party: `schedule`

**Advantages**:
- Simple, human-readable syntax
- Lightweight
- No dependencies

**Installation**:
```bash
pip install schedule
```

**Usage**:
```python
import schedule
import time

def cleanup_temp():
    """Cleanup temp directory."""
    print("Running temp cleanup...")

def cleanup_uploads():
    """Cleanup uploads directory."""
    print("Running uploads cleanup...")

# Schedule jobs
schedule.every().day.at("02:00").do(cleanup_temp)
schedule.every().day.at("02:30").do(cleanup_uploads)

# In FastAPI lifespan
while True:
    schedule.run_pending()
    time.sleep(60)
```

**Best For**: Simple applications, development environments

---

## 3. Scheduler Patterns

### 3.1 Cron Job Pattern

**Advantages**:
- System-level reliability
- No application dependency
- Easy to monitor with standard tools
- Persistent across application restarts

**Setup**:
```bash
# Crontab entry
0 2 * * * /opt/services/media-analysis/bin/cleanup.sh >> /var/log/media-analysis/cleanup.log 2>&1
```

**Script: cleanup.sh**:
```bash
#!/bin/bash
cd /opt/services/media-analysis
source venv/bin/activate
python -c "
from api.storage import StorageManager
manager = StorageManager()
result = manager.run_cleanup(dry_run=False)
print(f'Cleaned {result[\"files_removed\"]} files, freed {result[\"bytes_freed\"]} bytes')
"
```

**Monitoring**:
```bash
# Check last run
tail -20 /var/log/media-analysis/cleanup.log

# Add to monitoring
grep "ERROR" /var/log/media-analysis/cleanup.log
```

### 3.2 APScheduler Integration (Recommended for FastAPI)

**FastAPI Lifespan Integration**:
```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

@asynccontextmanager
async def lifespan(app):
    # Startup
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        cleanup_task,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_cleanup',
        name='Clean up old files'
    )
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

**Redis-Backed Scheduler for Distributed Systems**:
```python
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

jobstores = {
    'default': RedisJobStore(
        db=2,
        host='redis',
        port=6379,
        jobs_key='media_analysis.jobs',
        run_times_key='media_analysis.run_times'
    )
}

scheduler = BackgroundScheduler(jobstores=jobstores)
```

### 3.3 Hybrid Approach (Recommended)

**Primary**: APScheduler within application
**Fallback**: Cron job for reliability

```bash
# /opt/services/media-analysis/bin/cleanup.sh
#!/bin/bash

# Check if application scheduler is running
if curl -s http://localhost:8080/health | grep -q "ok"; then
    echo "$(date): Application healthy, letting app handle cleanup"
    exit 0
fi

# Fallback: Run cleanup directly
cd /opt/services/media-analysis
source venv/bin/activate
python -c "
from api.storage import StorageManager
manager = StorageManager()
result = manager.run_cleanup()
print(f'Fallback cleanup: {result}')
"
```

---

## 4. Permission Handling for Production

### 4.1 File Permission Best Practices

**Recommended Permissions**:
```bash
# Directory permissions (755)
chmod 755 /opt/services/media-analysis/storage
chmod 755 /opt/services/media-analysis/storage/*/

# File permissions (644)
find /opt/services/media-analysis/storage -type f -exec chmod 644 {} \;

# Script permissions (755)
chmod 755 /opt/services/media-analysis/bin/*.sh
```

**Python Permission Handling**:
```python
import os
import stat

def ensure_permissions(path):
    """Ensure correct permissions for path."""
    if os.path.isdir(path):
        os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    elif os.path.isfile(path):
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

def handle_permission_error(func, path, exc_info):
    """Handle permission errors gracefully."""
    if not os.access(path, os.W_OK):
        # Try to make file writable
        try:
            os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)
            func(path)
        except Exception as e:
            logger.error(f"Could not modify permissions on {path}: {e}")
            raise
    else:
        raise
```

### 4.2 umask Handling

```python
import os
import tempfile

# Set restrictive umask for new files
original_umask = os.umask(0o077)

def create_secure_temp_file():
    """Create temp file with secure permissions."""
    fd, path = tempfile.mkstemp(
        prefix='media_',
        suffix='.tmp',
        dir='/opt/services/media-analysis/storage/temp'
    )
    os.close(fd)
    os.umask(original_umask)
    return path

# Restore umask
os.umask(original_umask)
```

### 4.3 Ownership and Group Settings

```bash
#!/bin/bash
# setup-storage-permissions.sh

# Set ownership to application user
chown -R media:media /opt/services/media-analysis/storage

# Set group for shared access (if needed)
chgrp -R media /opt/services/media-analysis/storage

# Set SUID bit for specific operations (if needed)
# chmod u+s /opt/services/media-analysis/bin/cleanup-script.sh
```

### 4.4 Docker Volume Permissions

```dockerfile
# Dockerfile
RUN groupadd -r media && useradd -r -g media media
USER media

# Or at runtime
RUN chmod 755 /opt/services/media-analysis/storage
```

**docker-compose.yml**:
```yaml
volumes:
  - media-storage:/opt/services/media-analysis/storage

volumes:
  media-storage:
    driver: local
```

---

## 5. File Age Calculation Methods

### 5.1 Method 1: Modification Time (mtime)

```python
import os
import time
from datetime import datetime, timedelta

def get_file_age_mtime(file_path):
    """Get file age in seconds using modification time."""
    mtime = os.path.getmtime(file_path)
    return time.time() - mtime

def get_old_files(directory, max_age_seconds):
    """Get list of files older than max_age_seconds."""
    cutoff = time.time() - max_age_seconds
    old_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.getmtime(filepath) < cutoff:
                old_files.append(filepath)

    return old_files
```

### 5.2 Method 2: Access Time (atime)

```python
def get_file_age_atime(file_path):
    """Get file age using access time."""
    atime = os.stat(file_path).st_atime
    return time.time() - atime

def get_unaccessed_files(directory, max_age_seconds):
    """Get files not accessed in max_age_seconds."""
    cutoff = time.time() - max_age_seconds

    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.stat(filepath).st_atime < cutoff:
                yield filepath
```

### 5.3 Method 3: Creation Time (ctime) - Platform Specific

```python
import platform

def get_file_age_ctime(file_path):
    """Get file age using creation/birth time."""
    if platform.system() == 'Windows':
        ctime = os.path.getctime(file_path)
    else:
        # On Linux, ctime is metadata change time, not creation time
        stat_info = os.stat(file_path)
        ctime = stat_info.st_ctime
    return time.time() - ctime
```

### 5.4 Method 4: Custom Timestamp in Filename

```python
import re
from datetime import datetime

def extract_timestamp_from_filename(filename):
    """Extract timestamp from filename like frame_20240115_143022.jpg"""
    pattern = r'_(\d{8})_(\d{6})'
    match = re.search(pattern, filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        return (datetime.now() - dt).total_seconds()
    return None

def cleanup_by_filename_timestamp(directory, max_age_seconds):
    """Cleanup files based on embedded timestamp."""
    cutoff = time.time() - max_age_seconds

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            age = extract_timestamp_from_filename(filename)
            if age and age > max_age_seconds:
                os.remove(filepath)
```

### 5.5 Recommended Approach for Media Analysis

```python
from pathlib import Path
import time

class FileAgeCalculator:
    """Unified file age calculation with multiple strategies."""

    STRATEGY_MODIFICATION = 'mtime'
    STRATEGY_ACCESS = 'atime'
    STRATEGY_FILENAME = 'filename'

    def __init__(self, strategy=STRATEGY_MODIFICATION):
        self.strategy = strategy

    def get_age_seconds(self, file_path):
        """Get file age in seconds."""
        path = Path(file_path)

        if not path.exists():
            return None

        if self.strategy == self.STRATEGY_MODIFICATION:
            return time.time() - path.stat().st_mtime
        elif self.strategy == self.STRATEGY_ACCESS:
            return time.time() - path.stat().st_atime
        elif self.strategy == self.STRATEGY_FILENAME:
            return self._get_age_from_filename(path)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _get_age_from_filename(self, path):
        """Extract age from filename timestamp."""
        # Implement pattern matching based on your naming convention
        return None  # Fallback to mtime

    def filter_by_age(self, directory, max_age_seconds):
        """Get files older than max_age_seconds."""
        path = Path(directory)
        cutoff = time.time() - max_age_seconds

        old_files = []
        for file_path in path.rglob("*"):
            if file_path.is_file():
                age = self.get_age_seconds(file_path)
                if age and age > max_age_seconds:
                    old_files.append(file_path)

        return old_files
```

---

## 6. Error Handling Patterns

### 6.1 Comprehensive Error Handling Decorator

```python
import functools
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def handle_file_errors(operation_name):
    """Decorator for comprehensive file operation error handling."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except PermissionError as e:
                logger.error(f"Permission denied during {operation_name}: {e}")
                logger.error(f"Path: {kwargs.get('path', args[0] if args else 'unknown')}")
                # Attempt remediation
                return _handle_permission_error(operation_name, *args, **kwargs)
            except FileNotFoundError as e:
                logger.warning(f"File not found during {operation_name}: {e}")
                return {'success': False, 'error': 'file_not_found', 'path': str(e.filename)}
            except OSError as e:
                logger.error(f"OS error during {operation_name}: {e}")
                return {'success': False, 'error': 'os_error', 'details': str(e)}
            except Exception as e:
                logger.exception(f"Unexpected error during {operation_name}: {e}")
                return {'success': False, 'error': 'unknown', 'details': str(e)}
        return wrapper
    return decorator

def _handle_permission_error(operation_name, *args, **kwargs):
    """Attempt to remediate permission errors."""
    path = kwargs.get('path', args[0] if args else None)
    if path and os.path.exists(path):
        try:
            # Make file/directory writable
            os.chmod(path, 0o644)
            logger.info(f"Remediated permission for: {path}")
        except Exception as e:
            logger.error(f"Could not remediate permission: {e}")
    return {'success': False, 'error': 'permission_denied'}
```

### 6.2 Safe File Deletion with Verification

```python
import hashlib
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SafeDeleteManager:
    """Safe file deletion with verification and rollback support."""

    def __init__(self, trash_enabled=True, trash_path=None):
        self.trash_enabled = trash_enabled
        self.trash_path = trash_path or Path.home() / '.local' / 'share' / 'Trash'
        self.deleted_files = []

    def delete_with_verification(self, file_path, verify_checksum=True):
        """Delete file with pre-deletion verification."""
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return {'success': False, 'error': 'not_found'}

        # Calculate checksum before deletion
        checksum = None
        if verify_checksum and path.stat().st_size < 100 * 1024**3:  # Skip >100GB
            checksum = self._calculate_checksum(path)

        # Record for potential recovery
        file_info = {
            'path': str(path),
            'size': path.stat().st_size,
            'checksum': checksum,
            'mtime': path.stat().st_mtime
        }

        # Perform deletion
        try:
            if self.trash_enabled:
                self._move_to_trash(path)
            else:
                path.unlink()

            self.deleted_files.append(file_info)
            logger.info(f"Deleted: {file_path}")
            return {'success': True, 'file': file_info}
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            return {'success': False, 'error': str(e)}

    def _move_to_trash(self, path):
        """Move file to trash instead of permanent deletion."""
        from send2trash import send2trash
        send2trash(str(path))

    def _calculate_checksum(self, path):
        """Calculate MD5 checksum for verification."""
        md5 = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()

    def batch_delete(self, file_paths, **kwargs):
        """Delete multiple files with batch progress tracking."""
        results = []
        total = len(file_paths)

        for i, path in enumerate(file_paths, 1):
            result = self.delete_with_verification(path, **kwargs)
            result['index'] = i
            result['total'] = total
            results.append(result)

            if i % 100 == 0:
                logger.info(f"Batch delete progress: {i}/{total}")

        return results

    def get_deleted_files(self):
        """Get list of deleted files (for recovery)."""
        return self.deleted_files
```

### 6.3 Transactional File Operations

```python
import os
import shutil
import logging
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

@contextmanager
def file_transaction(directory, backup=True):
    """Context manager for transactional file operations."""
    backup_dir = Path(directory) / '.backup'
    backup_dir.mkdir(exist_ok=True)

    backup_files = []

    try:
        # Backup existing files
        if backup:
            for f in Path(directory).glob('*'):
                if f.is_file():
                    backup_path = backup_dir / f.name
                    shutil.copy2(f, backup_path)
                    backup_files.append(f)

        yield backup_files

        # Commit - remove backup on success
        for backup_file in backup_files:
            backup_file.unlink()

    except Exception as e:
        logger.error(f"Transaction failed, restoring backups: {e}")
        # Rollback
        for backup_file in backup_files:
            if backup_file.exists():
                backup_file.unlink()
            original_path = backup_file.parent / backup_file.name.replace('.backup', '')
            backup_file.rename(original_path)
        raise
```

### 6.4 Retry Logic for Transient Errors

```python
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def retry_on_transient_error(max_retries=3, delay=1, backoff=2):
    """Retry decorator for transient file system errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (OSError, IOError) as e:
                    # Check if it's a transient error
                    if e.errno in [5, 6, 121]:  # EIO, ENODEV, EREMOTEIO
                        logger.warning(f"Transient error, retrying ({retries + 1}/{max_retries}): {e}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                        retries += 1
                    else:
                        raise
                except Exception as e:
                    logger.error(f"Non-retryable error: {e}")
                    raise

            raise RuntimeError(f"Max retries ({max_retries}) exceeded")
        return wrapper
    return decorator

@retry_on_transient_error(max_retries=5, delay=0.5)
def safe_remove(file_path):
    """Remove file with retry logic for transient errors."""
    os.unlink(file_path)
```

### 6.5 Disk Space Monitoring Integration

```python
import shutil
import logging
import psutil

logger = logging.getLogger(__name__)

class DiskSpaceManager:
    """Monitor disk space and prioritize cleanup when low."""

    def __init__(self, min_free_bytes=None, min_free_percent=None):
        self.min_free_bytes = min_free_bytes or 5 * 1024**3  # 5GB default
        self.min_free_percent = min_free_percent or 10  # 10% default

    def check_disk_space(self, path):
        """Check disk space at given path."""
        disk = psutil.disk_usage(path)
        free_gb = disk.free / (1024**3)
        percent_free = disk.free / disk.total * 100

        return {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': free_gb,
            'percent_free': percent_free
        }

    def needs_cleanup(self, path):
        """Determine if cleanup is needed based on disk space."""
        stats = self.check_disk_space(path)

        if stats['free_gb'] * 1024**3 < self.min_free_bytes:
            return True, f"Free space below {self.min_free_bytes / (1024**3):.1f}GB"

        if stats['percent_free'] < self.min_free_percent:
            return True, f"Free space below {self.min_free_percent}%"

        return False, "Disk space OK"

    def get_priority_cleanup_order(self, storage_manager):
        """Get cleanup order based on urgency."""
        # Cleanup temp first (24h), then uploads (7d), then frames (30d)
        return [
            ('temp', 86400),
            ('uploads', 604800),
            ('frames', 2592000),
            ('contact_sheets', 2592000),
        ]
```

---

## 7. Summary and Recommendations

### Recommended Tech Stack

| Component | Recommendation | Justification |
|-----------|---------------|---------------|
| Path handling | `pathlib` | Modern, object-oriented, built-in |
| Directory operations | `shutil` | Robust, handles edge cases |
| Safe deletion | `send2trash` | Reversible, prevents accidental data loss |
| Scheduling | APScheduler | Built-in to FastAPI, persistent options |
| Error handling | Custom decorator pattern | Comprehensive, maintainable |

### Implementation Priority

1. **High Priority**: StorageManager class with cleanup methods
2. **Medium Priority**: Scheduler integration with APScheduler
3. **Medium Priority**: Error handling and logging
4. **Low Priority**: Advanced features (trash, monitoring)

### Risk Mitigation Summary

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Permission errors | Medium | High | umask, error recovery, logging |
| Accidental deletion | Low | Critical | send2trash, dry_run, backup |
| Scheduler conflicts | Medium | Medium | Idempotent ops, lock files |
| Disk full | High | High | Priority cleanup, monitoring |
| Large file ops | Medium | Medium | Batch processing, progress logging |

---

## 8. References

### Python Documentation
- [pathlib - Object-oriented filesystem paths](https://docs.python.org/3/library/pathlib.html)
- [shutil - High-level file operations](https://docs.python.org/3/library/shutil.html)
- [os - Miscellaneous operating system interfaces](https://docs.python.org/3/library/os.html)

### Third-Party Libraries
- [send2trash - Send files to trash instead of deleting](https://pypi.org/project/Send2Trash/)
- [APScheduler - In-process task scheduler](https://apscheduler.readthedocs.io/)
- [schedule - Job scheduling for humans](https://schedule.readthedocs.io/)

### Best Practices
- [Python File System Operations Best Practices](https://realpython.com/working-with-files-in-python/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Docker Volume Permissions](https://docs.docker.com/storage/volumes/)
