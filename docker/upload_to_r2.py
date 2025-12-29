#!/usr/bin/env python3
"""
R2 Upload Script for ComfyUI Output Sync.

Uploads files to Cloudflare R2 with retry logic and organized folder structure.
Designed for use with r2_sync.sh inotifywait daemon.

Author: oz
Model: claude-opus-4-5
Date: 2025-12-29
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import time

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ImportError:
    print("[R2] Error: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='[R2] %(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class R2Uploader:
    """Cloudflare R2 file uploader with retry logic."""

    def __init__(self):
        self.endpoint = os.environ.get(
            'R2_ENDPOINT',
            'https://8755d4118d392ca7e1a6e1e5733cf55f.eu.r2.cloudflarestorage.com'
        )
        self.bucket = os.environ.get('R2_BUCKET', 'runpod')
        # Support both naming conventions
        self.access_key = os.environ.get('R2_ACCESS_KEY_ID') or os.environ.get('R2_ACCESS_KEY')
        self.secret_key = os.environ.get('R2_SECRET_ACCESS_KEY') or os.environ.get('R2_SECRET_KEY')

        if not self.access_key or not self.secret_key:
            logger.error("R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY environment variables required")
            raise ValueError("Missing R2 credentials")

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4', retries={'max_attempts': 3, 'mode': 'adaptive'}),
            region_name='auto'
        )
        logger.info(f"R2 client ready: {self.bucket}")

    def upload_file(self, local_path: str, remote_prefix: str = "outputs", max_retries: int = 3) -> bool:
        local_path = Path(local_path)
        if not local_path.exists():
            logger.error(f"File not found: {local_path}")
            return False

        date_folder = datetime.now().strftime('%Y-%m-%d')
        remote_key = f"{remote_prefix}/{date_folder}/{local_path.name}"
        file_size = local_path.stat().st_size
        logger.info(f"Uploading: {local_path.name} ({file_size / 1024 / 1024:.2f} MB)")

        for attempt in range(1, max_retries + 1):
            try:
                if file_size > 100 * 1024 * 1024:
                    self._multipart_upload(local_path, remote_key)
                else:
                    self.client.upload_file(str(local_path), self.bucket, remote_key)
                logger.info(f"Uploaded: s3://{self.bucket}/{remote_key}")
                return True
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {error_code}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Upload failed: {e}")
                    return False
            except Exception as e:
                logger.error(f"Error: {e}")
                return False
        return False

    def _multipart_upload(self, local_path: Path, remote_key: str, chunk_size: int = 50 * 1024 * 1024):
        file_size = local_path.stat().st_size
        mpu = self.client.create_multipart_upload(Bucket=self.bucket, Key=remote_key)
        upload_id = mpu['UploadId']
        parts = []
        try:
            with open(local_path, 'rb') as f:
                part_number = 1
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    response = self.client.upload_part(
                        Bucket=self.bucket, Key=remote_key,
                        PartNumber=part_number, UploadId=upload_id, Body=data
                    )
                    parts.append({'PartNumber': part_number, 'ETag': response['ETag']})
                    logger.info(f"  Part {part_number}: {min((part_number * chunk_size / file_size) * 100, 100):.0f}%")
                    part_number += 1
            self.client.complete_multipart_upload(
                Bucket=self.bucket, Key=remote_key, UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
        except Exception as e:
            self.client.abort_multipart_upload(Bucket=self.bucket, Key=remote_key, UploadId=upload_id)
            raise

    def test_connection(self) -> bool:
        try:
            self.client.list_objects_v2(Bucket=self.bucket, MaxKeys=1)
            logger.info(f"Connection OK: {self.bucket}")
            return True
        except ClientError as e:
            logger.error(f"Connection failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Upload files to Cloudflare R2')
    parser.add_argument('files', nargs='*', help='Files to upload')
    parser.add_argument('--test', action='store_true', help='Test R2 connection')
    parser.add_argument('--prefix', default='outputs', help='R2 key prefix')
    args = parser.parse_args()

    try:
        uploader = R2Uploader()
    except ValueError:
        sys.exit(1)

    if args.test:
        sys.exit(0 if uploader.test_connection() else 1)

    if not args.files:
        parser.print_help()
        sys.exit(1)

    success = sum(1 for f in args.files if uploader.upload_file(f, args.prefix))
    logger.info(f"Complete: {success}/{len(args.files)}")
    sys.exit(0 if success == len(args.files) else 1)


if __name__ == '__main__':
    main()
