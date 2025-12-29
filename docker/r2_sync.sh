#!/bin/bash
# R2 Sync Daemon - watches ComfyUI output directory and uploads new files
#
# Author: oz
# Model: claude-opus-4-5
# Date: 2025-12-29

set -e

OUTPUT_DIR="${COMFYUI_OUTPUT_DIR:-/workspace/ComfyUI/output}"
LOG_FILE="/var/log/r2_sync.log"
UPLOAD_SCRIPT="/upload_to_r2.py"

# File patterns to watch (images, videos, audio)
WATCH_PATTERNS="\.png$|\.jpg$|\.jpeg$|\.webp$|\.mp4$|\.webm$|\.gif$|\.wav$|\.mp3$|\.flac$"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check dependencies
if ! command -v inotifywait &> /dev/null; then
    log "ERROR: inotifywait not found. Install: apt-get install inotify-tools"
    exit 1
fi

if [ ! -f "$UPLOAD_SCRIPT" ]; then
    log "ERROR: Upload script not found: $UPLOAD_SCRIPT"
    exit 1
fi

# Check R2 credentials (support both naming conventions)
R2_ACCESS="${R2_ACCESS_KEY_ID:-$R2_ACCESS_KEY}"
R2_SECRET="${R2_SECRET_ACCESS_KEY:-$R2_SECRET_KEY}"
if [ -z "$R2_ACCESS" ] || [ -z "$R2_SECRET" ]; then
    log "ERROR: R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY required"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log "Starting R2 sync daemon"
log "Watching: $OUTPUT_DIR"

# Watch for new files and upload them
inotifywait -m -r -e close_write --format '%w%f' "$OUTPUT_DIR" 2>/dev/null | while read filepath; do
    if echo "$filepath" | grep -qE "$WATCH_PATTERNS"; then
        sleep 1  # Ensure file is fully written
        if [ -f "$filepath" ]; then
            log "New file: $filepath"
            (
                python3 "$UPLOAD_SCRIPT" "$filepath" >> "$LOG_FILE" 2>&1
                [ $? -eq 0 ] && log "Uploaded: $(basename "$filepath")" || log "FAILED: $(basename "$filepath")"
            ) &
        fi
    fi
done
