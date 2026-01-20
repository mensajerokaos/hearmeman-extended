# File Storage Organization System - Implementation Plan

## Executive Summary
Implement structured file storage system for media analysis outputs with hierarchical organization by date, source type, and analysis type. Base path: /opt/services/media-analysis/data/outputs.

## Phase 1: Storage Directory Structure

### Step 1.1: Create Directory Structure Script
- File: /opt/services/media-analysis/scripts/create_storage_structure.sh
- Code:
```bash
#!/bin/bash
BASE_DIR="${MEDIA_OUTPUT_BASE:-/opt/services/media-analysis/data/outputs}"

# Create hierarchical structure
mkdir -p "$BASE_DIR/{audio,video,image,document}/{youtube,upload,transcription,直播}/{raw,processed,analysis}"

# Set permissions
chmod -R 755 "$BASE_DIR"
chown -R media-analysis:media-analysis "$BASE_DIR"

echo "Storage structure created at $BASE_DIR"
```

### Step 1.2: Create Storage Manager Module
- File: /opt/services/media-analysis/src/storage/manager.py
- Code:
```python
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib

class StorageManager:
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getenv("MEDIA_OUTPUT_BASE", "/opt/services/media-analysis/data/outputs"))
    
    def get_storage_path(self, source_type: str, source_id: str, file_type: str = "raw") -> Path:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.base_path / source_type / source_id / date_str / file_type
    
    def ensure_directory(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def generate_unique_filename(self, original_filename: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(f"{original_filename}{timestamp}".encode()).hexdigest()[:8]
        return f"{Path(original_filename).stem}_{timestamp}_{hash_suffix}{Path(original_filename).suffix}"
```

## Phase 2: File Organization Logic

### Step 2.1: Create File Classifier
- File: /opt/services/media-analysis/src/storage/classifier.py
- Code:
```python
from enum import Enum
from pathlib import Path
import mimetypes

class SourceType(Enum):
    YOUTUBE = "youtube"
    UPLOAD = "upload"
    TRANSCRIPTION = "transcription"
    LIVESTREAM = "直播"

class FileClassifier:
    @staticmethod
    def classify_by_mime(filepath: Path) -> str:
        mime, _ = mimetypes.guess_type(str(filepath))
        if mime and mime.startswith("video"):
            return "video"
        elif mime and mime.startswith("audio"):
            return "audio"
        elif mime and mime.startswith("image"):
            return "image"
        return "document"
```

## Phase 3: Integration with API

### Step 3.1: Update Upload Endpoint
- File: /opt/services/media-analysis/src/api/endpoints/upload.py
- Code:
```python
from storage.manager import StorageManager

storage = StorageManager()

@router.post("/upload")
async def upload_file(file: UploadFile, source_type: str = "upload"):
    storage_path = storage.get_storage_path(source_type, "default", "raw")
    storage.ensure_directory(storage_path)
    unique_name = storage.generate_unique_filename(file.filename)
    filepath = storage_path / unique_name
    
    with open(filepath, "wb") as f:
        f.write(await file.read())
    
    return {"path": str(filepath), "size": filepath.stat().st_size}
```

## Phase 4: Testing

### Step 4.1: Test Directory Creation
- Bash: `bash /opt/services/media-analysis/scripts/create_storage_structure.sh`
- Expected: "Storage structure created" message

### Step 4.2: Test Storage Manager
- Bash: `cd /opt/services/media-analysis && python -c "from storage.manager import StorageManager; s = StorageManager(); print(s.get_storage_path('youtube', 'abc123'))"`
- Expected: Path string matching pattern

## Rollback
- Bash: `rm -rf /opt/services/media-analysis/data/outputs`
- Verification: Directory no longer exists

## Bead Structure
| Phase | Bead Title | Parallel With | Blocked By |
|-------|------------|---------------|------------|
| 1 | [PRD] ma-23 - Directory Structure | - | - |
| 2 | [PRD] ma-23 - Storage Manager | p1 | - |
| 3 | [PRD] ma-23 - API Integration | p2 | - |
| 4 | [PRD] ma-23 - Testing | p3 | - |
