#!/usr/bin/env python3
"""
Create Dance Analysis Job Script

Sends dance choreography video to the media analysis API with detailed
movement physics prompts covering garment, hair, motion blur, and foot contact.
"""

import httpx
import json
import asyncio
from uuid import UUID

VIDEO_PATH = "/mnt/m/solar/aria-cruz-ai/01-reto-freelancer/video/video_analysis/cosplayer-frieren-vibe-check-dc-Cody.mp4"
API_BASE_URL = "http://localhost:8000"

# Movement analysis prompts
ANALYSIS_PROMPTS = {
    "garment_physics": (
        "Analyze how the fabric moves and drapes during the choreography. "
        "Consider gravity effects, inertia, and body collision. "
        "Describe the cloth simulation behavior needed for realistic reproduction, "
        "including damping coefficient, stiffness, and collision radius."
    ),
    "hair_dynamics": (
        "Track hair movement including strands, flow direction, wind effects, "
        "and collision with shoulders/face. Note any hair clips, constraints, "
        "or accessories. Estimate strand count and identify collision points. "
        "Document key frames where significant movement occurs."
    ),
    "motion_blur": (
        "Identify all regions with motion blur throughout the video. "
        "Analyze blur direction (radial, arc, tangential), magnitude, and "
        "temporal extent in frames. Preserve blur patterns when generating "
        "new frames - they indicate high-speed movement."
    ),
    "foot_contact": (
        "Analyze foot placement and ground contact timing throughout the choreography. "
        "Note weight distribution, balance shifts, and pivot points. "
        "Document contact pressure (full weight vs partial pivot) frame by frame."
    ),
    "limb_motion": (
        "Track arm and leg movement trajectories. Identify rotation, swing, "
        "and pivot movements. Note acceleration changes and synchronization "
        "between limbs. Measure range of motion for each joint."
    ),
    "overall_physics": (
        "Ensure overall body physics remain consistent throughout: "
        "center of gravity stability, balance maintenance, and momentum conservation. "
        "Verify no unnatural jumps or physics violations in movement."
    )
}


async def create_job():
    """Create analysis job with dance video and movement prompts."""

    payload = {
        "media_type": "video",
        "source_url": VIDEO_PATH,
        "metadata_json": {
            "video_name": "cosplayer-frieren-vibe-check-dc-Cody",
            "analysis_type": "movement_physics",
            "description": "Dance choreography analysis with detailed movement physics",
            "focus_areas": [
                "garment_movement",
                "hair_dynamics",
                "motion_blur_preservation",
                "foot_contact_detection",
                "limb_motion_patterns"
            ],
            "analysis_prompts": ANALYSIS_PROMPTS
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Creating analysis job...")
        print(f"Video path: {VIDEO_PATH}")
        print(f"Analysis type: movement_physics")
        print(f"Focus areas: {payload['metadata_json']['focus_areas']}")
        print()

        response = await client.post(
            f"{API_BASE_URL}/api/v1/jobs",
            json=payload
        )

        if response.status_code != 201:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None

        job = response.json()
        job_id = job["id"]

        print("✓ Job created successfully!")
        print(f"Job ID: {job_id}")
        print(f"Status: {job['status']}")
        print(f"Created at: {job['created_at']}")
        print()
        print("Job details:")
        print(json.dumps(job, indent=2, default=str))

        return job_id


async def main():
    """Main entry point."""
    job_id = await create_job()

    if job_id:
        # Save job ID to file for later use
        with open("/tmp/dance_job_id.txt", "w") as f:
            f.write(str(job_id))
        print(f"\nJob ID saved to /tmp/dance_job_id.txt")
    else:
        print("Failed to create job")


if __name__ == "__main__":
    asyncio.run(main())
