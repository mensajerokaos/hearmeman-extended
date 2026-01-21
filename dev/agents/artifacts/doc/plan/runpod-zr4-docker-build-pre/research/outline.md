---
topic: Build and test Docker image locally for ComfyUI with SteadyDancer, mmcv, mmpose, flash-attn dependencies
created: 2026-01-21T06:13:00+00:00
sections: 5
format: reference
---

# Outline: RunPod SteadyDancer Docker Build and Test

## Executive Summary
This document details the process of building and testing a Docker image for ComfyUI with SteadyDancer video generation capabilities. The build includes OpenMMLab dependencies (mmcv, mmdet, mmpose), DWPose for pose estimation, and Flash Attention with xformers fallback for memory-efficient attention mechanisms.

## Section 1: Prerequisites and Dependencies
- **Purpose**: Document all required dependencies for the Docker build
- **Key Points**:
  - OpenMMLab stack versions and compatibility
  - CUDA requirements and PyTorch version pinning
  - Flash Attention installation with fallback strategy
- **Sources**: Web findings, local codebase

## Section 2: Docker Build Configuration
- **Purpose**: Define Dockerfile changes and build arguments
- **Key Points**:
  - Build ARGs for conditional installation
  - Multi-stage build considerations
  - Environment variable configuration
- **Sources**: Existing Dockerfile patterns

## Section 3: Model Integration
- **Purpose**: Document model download and configuration
- **Key Points**:
  - SteadyDancer variant selection (fp8/fp16/GGUF)
  - HuggingFace model download process
  - Model directory structure
- **Sources**: download_models.sh, existing workflows

## Section 4: Local Testing Procedures
- **Purpose**: Define testing workflow for local validation
- **Key Points**:
  - Docker compose startup
  - ComfyUI workflow validation
  - Error checking and debugging
- **Sources**: CLAUDE.md testing checklist

## Section 5: Production Deployment
- **Purpose**: Document deployment to RunPod
- **Key Points**:
  - Container configuration for production
  - Resource allocation (VRAM, storage)
  - Monitoring and troubleshooting
- **Sources**: CLAUDE.md deployment section

## Appendix
- Sources & References
- Quick Reference Card
- Troubleshooting Guide
