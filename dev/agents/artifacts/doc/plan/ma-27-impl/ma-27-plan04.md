# MiniMax Vision MCP Research - Implementation Plan

## Executive Summary
Research and document MiniMax Vision MCP integration patterns. Create integration guide for MiniMax-M2-1.5M-Vision model in the media analysis pipeline.

## Phase 1: Research and Documentation

### Step 1.1: Create Research Document
- File: /opt/services/media-analysis/docs/vision/minimax-research.md
- Code:
```markdown
# MiniMax Vision MCP Integration Research

## Model Specifications
- Model: MiniMax-M2-1.5M-Vision
- Context Window: 128K tokens
- Vision: 1.5M parameter vision encoder
- API: REST + MCP

## Integration Options

### Option 1: Direct API
```python
import requests

response = requests.post(
    "https://api.minimax.chat/v1/vision/analyze",
    headers={"Authorization": f"Bearer {API_KEY}"},
    files={"image": open("image.jpg", "rb")},
    data={"prompt": "Describe this image in detail"}
)
```

### Option 2: MCP Protocol
```python
from mcp_client import MCPClient

client = MCPClient("minimax-vision")
result = await client.call_tool("analyze_image", {"image": "path.jpg"})
```

## Pricing
- Input: $0.001 per 1K tokens
- Output: $0.003 per 1K tokens
- Vision: $0.01 per image
```

## Phase 2: Client Implementation

### Step 2.1: Create MiniMax Vision Client
- File: /opt/services/media-analysis/src/vision/providers/minimax.py
- Code:
```python
import os
from typing import Optional
import aiohttp
from vision.base import VisionProvider

class MiniMaxVisionProvider(VisionProvider):
    BASE_URL = "https://api.minimax.chat/v1/vision"
    
    async def analyze(self, image_path: str, prompt: str = "Describe this image") -> str:
        api_key = os.getenv("MINIMAX_API_KEY")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/analyze",
                headers={"Authorization": f"Bearer {api_key}"},
                data={"prompt": prompt},
                files={"image": open(image_path, "rb")}
            ) as response:
                return await response.json()
```

## Phase 3: Integration Guide

### Step 3.1: Create Integration Guide
- File: /opt/services/media-analysis/docs/integration/minimax-guide.md
- Code:
```markdown
# MiniMax Vision Integration Guide

## Prerequisites
1. Obtain API key from MiniMax dashboard
2. Set environment variable: `MINIMAX_API_KEY`
3. Install aiohttp: `pip install aiohttp`

## Quick Start
```python
from vision.providers.minimax import MiniMaxVisionProvider

provider = MiniMaxVisionProvider()
result = await provider.analyze("image.jpg")
print(result.content)
```

## Error Handling
- Rate limiting: Implement exponential backoff
- Invalid image: Return error with message
- API down: Fallback to next provider
```

## Phase 4: Testing

### Step 4.1: Test MiniMax Integration
- Bash: `cd /opt/services/media-analysis && python -c "from vision.providers.minimax import MiniMaxVisionProvider; p = MiniMaxVisionProvider(); print('Provider initialized')"`
- Expected: No errors

### Step 4.2: Test with Real Image
- Bash: `cd /opt/services/media-analysis && python -c "import asyncio; from vision.providers.minimax import MiniMaxVisionProvider; asyncio.run(MiniMaxVisionProvider().analyze('tests/fixtures/sample.jpg'))"`
- Expected: JSON response with analysis

## Rollback
- Bash: `cd /opt/services/media-analysis && git checkout src/vision/providers/minimax.py`
- Verification: Original file restored

## Bead Structure
| Phase | Bead Title | Parallel With | Blocked By |
|-------|------------|---------------|------------|
| 1 | [PRD] ma-27 - Research Doc | - | - |
| 2 | [PRD] ma-27 - Client Library | p1 | - |
| 3 | [PRD] ma-27 - Integration Guide | p2 | - |
| 4 | [PRD] ma-27 - Testing | p3 | - |
