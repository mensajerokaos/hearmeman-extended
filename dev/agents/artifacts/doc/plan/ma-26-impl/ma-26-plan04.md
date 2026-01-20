# Vision Fallback Chain Test - Implementation Plan

## Executive Summary
Implement comprehensive tests for vision fallback chain: Qwen3-VL → Gemini → GPT-5 → MiniMax Vision. Ensure each provider is tested and fallback logic is verified.

## Phase 1: Test Framework Setup

### Step 1.1: Create Test Configuration
- File: /opt/services/media-analysis/tests/vision/fallback_config.py
- Code:
```python
import os

VISION_PROVIDERS = {
    "qwen3-vl": {
        "enabled": True,
        "model": "Qwen/Qwen2.5-VL-72B-Instruct",
        "max_tokens": 4096,
        "api_key": os.getenv("QWEN_API_KEY")
    },
    "gemini": {
        "enabled": True,
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 8192,
        "api_key": os.getenv("GEMINI_API_KEY")
    },
    "gpt-5": {
        "enabled": True,
        "model": "gpt-5",
        "max_tokens": 16384,
        "api_key": os.getenv("OPENAI_API_KEY")
    },
    "minimax": {
        "enabled": True,
        "model": "MiniMax-M2-1.5M-Vision",
        "max_tokens": 8192,
        "api_key": os.getenv("MINIMAX_API_KEY")
    }
}
```

## Phase 2: Fallback Chain Implementation

### Step 2.1: Create Fallback Router
- File: /opt/services/media-analysis/src/vision/fallback_chain.py
- Code:
```python
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class VisionResult:
    success: bool
    provider: str
    content: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0

class VisionFallbackChain:
    PROVIDERS = ["qwen3-vl", "gemini", "gpt-5", "minimax"]
    
    async def analyze(self, image_path: str) -> VisionResult:
        for provider in self.PROVIDERS:
            try:
                result = await self._call_provider(provider, image_path)
                if result.success:
                    return result
            except Exception as e:
                continue
        return VisionResult(success=False, provider="none", error="All providers failed")
```

## Phase 3: Provider Implementations

### Step 3.1: Qwen3-VL Implementation
- File: /opt/services/media-analysis/src/vision/providers/qwen.py
- Code:
```python
from vision.base import VisionProvider

class QwenVisionProvider(VisionProvider):
    async def analyze(self, image_path: str) -> str:
        # Implementation using Qwen API
        pass
```

### Step 3.2: Gemini Implementation
- File: /opt/services/media-analysis/src/vision/providers/gemini.py
- Code:
```python
from vision.base import VisionProvider

class GeminiVisionProvider(VisionProvider):
    async def analyze(self, image_path: str) -> str:
        # Implementation using Gemini API
        pass
```

## Phase 4: Test Suite

### Step 4.1: Unit Tests for Each Provider
- File: /opt/services/media-analysis/tests/vision/test_providers.py
- Code:
```python
import pytest

@pytest.mark.asyncio
async def test_qwen_vision():
    provider = QwenVisionProvider()
    result = await provider.analyze("tests/fixtures/sample.jpg")
    assert result.success
    assert "error" not in result

@pytest.mark.asyncio
async def test_fallback_chain():
    chain = VisionFallbackChain()
    result = await chain.analyze("tests/fixtures/sample.jpg")
    assert result.success
    assert result.provider in VisionFallbackChain.PROVIDERS
```

### Step 4.2: Run Test Suite
- Bash: `cd /opt/services/media-analysis && python -m pytest tests/vision/ -v --tb=short`
- Expected: All tests pass

## Rollback
- Bash: `cd /opt/services/media-analysis && git checkout tests/vision/`
- Verification: Original test files restored

## Bead Structure
| Phase | Bead Title | Parallel With | Blocked By |
|-------|------------|---------------|------------|
| 1 | [PRD] ma-26 - Test Framework | - | - |
| 2 | [PRD] ma-26 - Fallback Chain | p1 | - |
| 3 | [PRD] ma-26 - Provider Tests | p2 | - |
| 4 | [PRD] ma-26 - Full Test Suite | p3 | - |
