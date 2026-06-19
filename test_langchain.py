#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""LangChain Refactoring Verification Test"""
import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

print("=" * 60)
print("LangChain Refactoring Verification Test")
print("=" * 60)

# Test 1: Imports
print("\n[1/4] Testing imports...")
from core.models import create_zhipu_llm, create_deepseek_llm
print("  OK: Models")

from core.prompts import video_analysis_prompt, script_generation_prompt, STYLE_DESCRIPTIONS
styles = list(STYLE_DESCRIPTIONS.keys())
print(f"  OK: Prompts - Styles: {styles}")

from core.chains import VideoAnalysisChain, ScriptGenerationChain
print("  OK: Chains")

from services.video_service import VideoService
print("  OK: VideoService")

from services.audio_service import AudioService
print("  OK: AudioService")

from core.pipeline import NarrationPipeline, create_pipeline
print("  OK: Pipeline")

# Test 2: Pipeline Creation
print("\n[2/4] Testing Pipeline creation...")
pipeline = NarrationPipeline()
print(f"  Style: {pipeline.style}")
print(f"  Max scenes: {pipeline.max_scenes}")
print(f"  Dirs: {list(pipeline.dirs.keys())}")
print("  OK: Pipeline created")

# Test 3: Chains
print("\n[3/4] Testing Chains...")
va_chain = VideoAnalysisChain(cache_enabled=True)
print(f"  OK: VideoAnalysisChain")

sg_chain = ScriptGenerationChain(style="悬疑", use_theme_context=True)
print(f"  OK: ScriptGenerationChain")

# Test 4: Services
print("\n[4/4] Testing Services...")
video_service = VideoService(scene_threshold=35.0)
print(f"  OK: VideoService")

audio_service = AudioService(voice="zh-CN-YunxiNeural")
print(f"  OK: AudioService")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
