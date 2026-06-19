"""
背景音乐功能测试脚本

用于测试 BGM 的添加、循环、淡出和音量调节功能
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.audio_service import AudioService
from config import BGM_FADE_DURATION


def test_bgm_functions():
    """Test BGM related functions"""
    print("=" * 60)
    print("BGM Feature Test")
    print("=" * 60)
    
    audio_service = AudioService()
    
    # Test 1: Check add_background_music method exists
    print("\n[Test 1] Checking add_background_music method...")
    assert hasattr(audio_service, 'add_background_music'), "add_background_music method not found"
    print("[OK] add_background_music method exists")
    
    # Test 2: Check _loop_audio method exists
    print("\n[Test 2] Checking _loop_audio method...")
    assert hasattr(audio_service, '_loop_audio'), "_loop_audio method not found"
    print("[OK] _loop_audio method exists")
    
    # Test 3: Check config BGM configuration
    print("\n[Test 3] Checking config configuration...")
    assert BGM_FADE_DURATION > 0, "BGM_FADE_DURATION should be greater than 0"
    print(f"[OK] BGM_FADE_DURATION = {BGM_FADE_DURATION}s")
    
    # Test 4: Check CompositionService supports BGM parameters
    print("\n[Test 4] Checking CompositionService.compose_sync_video method...")
    from services.composition_service import CompositionService
    import inspect
    sig = inspect.signature(CompositionService.compose_sync_video)
    params = list(sig.parameters.keys())
    assert 'bgm_path' in params, "compose_sync_video missing bgm_path parameter"
    assert 'bgm_volume' in params, "compose_sync_video missing bgm_volume parameter"
    print(f"[OK] compose_sync_video signature includes bgm_path and bgm_volume")
    
    # Test 5: Check Pipeline supports BGM parameters
    print("\n[Test 5] Checking NarrationPipeline.execute method...")
    from core.pipeline import NarrationPipeline
    sig = inspect.signature(NarrationPipeline.execute)
    params = list(sig.parameters.keys())
    assert 'bgm_path' in params, "execute missing bgm_path parameter"
    assert 'bgm_volume' in params, "execute missing bgm_volume parameter"
    print(f"[OK] execute signature includes bgm_path and bgm_volume")
    
    # Test 6: Check helper function supports BGM parameters
    print("\n[Test 6] Checking generate_narration_video helper function...")
    from core.pipeline import generate_narration_video
    sig = inspect.signature(generate_narration_video)
    params = list(sig.parameters.keys())
    assert 'bgm_path' in params, "generate_narration_video missing bgm_path parameter"
    assert 'bgm_volume' in params, "generate_narration_video missing bgm_volume parameter"
    print(f"[OK] generate_narration_video signature includes bgm_path and bgm_volume")
    
    # Test 7: Check App UI components
    print("\n[Test 7] Checking App UI components...")
    from app import create_ui
    # Just check if it can be imported, actual UI test requires manual verification
    print("[OK] App UI can be imported")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nNote: Actual BGM processing requires manual testing with video and audio files.")
    print("Usage:")
    print("1. Start Web UI: python app.py")
    print("2. Visit http://127.0.0.1:7860")
    print("3. Upload video file and background music file")
    print("4. Adjust volume slider")
    print("5. Click generate button")


if __name__ == "__main__":
    test_bgm_functions()
