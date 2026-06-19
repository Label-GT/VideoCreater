"""
单元测试模块
测试 LangChain Chains 和服务
"""
import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestVideoService:
    """测试视频服务"""
    
    def test_video_service_init(self):
        """测试初始化"""
        from services.video_service import VideoService
        
        service = VideoService()
        assert service.scene_threshold == 35.0
        assert service.min_scene_duration == 1.0
        
        service2 = VideoService(scene_threshold=40.0, min_scene_duration=2.0)
        assert service2.scene_threshold == 40.0
        assert service2.min_scene_duration == 2.0
    
    @patch('services.video_service.subprocess.run')
    def test_get_video_info(self, mock_run):
        """测试获取视频信息"""
        from services.video_service import VideoService
        
        # Mock ffprobe 输出
        mock_stream_data = {
            "streams": [{
                "width": 1920,
                "height": 1080,
                "codec_name": "h264",
                "r_frame_rate": "30/1"
            }]
        }
        
        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_stream_data),
            stderr=""
        )
        mock_run.return_value.stdout = json.dumps(mock_stream_data)
        
        # 第二次调用返回时长
        mock_run.side_effect = [
            MagicMock(stdout=json.dumps(mock_stream_data)),
            MagicMock(stdout="120.5")
        ]
        
        service = VideoService()
        # 注意：这个测试需要真实的视频文件，暂时跳过
        pytest.skip("需要真实视频文件")


class TestVideoAnalysisChain:
    """测试视频分析 Chain"""
    
    def test_video_analysis_chain_init(self):
        """测试初始化"""
        from core.chains import VideoAnalysisChain
        
        chain = VideoAnalysisChain()
        assert chain.cache_enabled == True
        
        chain2 = VideoAnalysisChain(cache_enabled=False)
        assert chain2.cache_enabled == False
    
    def test_create_video_analysis_chain(self):
        """测试创建 Chain"""
        from core.chains import create_video_analysis_chain
        
        chain = create_video_analysis_chain()
        assert chain is not None
    
    def test_encode_image(self):
        """测试图片编码"""
        from core.chains.video_analysis_chain import encode_image
        
        # 创建一个临时测试图片
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            # 写入简单的 PNG 文件头
            f.write(b'\x89PNG\r\n\x1a\n')
            temp_path = f.name
        
        try:
            encoded = encode_image(temp_path)
            assert encoded.startswith('iVBOR')
        finally:
            os.unlink(temp_path)


class TestScriptGenerationChain:
    """测试文案生成 Chain"""
    
    def test_script_generation_chain_init(self):
        """测试初始化"""
        from core.chains import ScriptGenerationChain
        
        chain = ScriptGenerationChain(style="悬疑")
        assert chain.style == "悬疑"
        assert chain.use_theme_context == True
        
        chain2 = ScriptGenerationChain(style="幽默", use_theme_context=False)
        assert chain2.style == "幽默"
        assert chain2.use_theme_context == False
    
    def test_invalid_style(self):
        """测试无效风格"""
        from core.chains import ScriptGenerationChain
        
        with pytest.raises(ValueError):
            ScriptGenerationChain(style="无效风格")
    
    def test_create_script_generation_chain(self):
        """测试创建 Chain"""
        from core.chains import create_script_generation_chain
        
        chain = create_script_generation_chain(style="悬疑")
        assert chain is not None
        
        chain2 = create_script_generation_chain(style="热血")
        assert chain2 is not None
    
    def test_calculate_max_chars(self):
        """测试最大字符数计算"""
        from core.chains.script_generation_chain import calculate_max_chars
        
        assert calculate_max_chars(3.0) == 12
        assert calculate_max_chars(5.0, 4.0) == 20
        assert calculate_max_chars(2.5, 5.0) == 12


class TestAudioService:
    """测试音频服务"""
    
    def test_audio_service_init(self):
        """测试初始化"""
        from services.audio_service import AudioService
        
        service = AudioService()
        assert service.voice == "zh-CN-YunxiNeural"
        
        service2 = AudioService(voice="en-US-JennyNeural")
        assert service2.voice == "en-US-JennyNeural"
    
    @pytest.mark.skip(reason="需要 Edge TTS API 调用")
    def test_text_to_speech(self):
        """测试文本转语音"""
        from services.audio_service import AudioService
        
        service = AudioService()
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            temp_path = f.name
        
        try:
            service.text_to_speech("测试文本", temp_path)
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestNarrationPipeline:
    """测试完整 Pipeline"""
    
    def test_pipeline_init(self):
        """测试 Pipeline 初始化"""
        from core.pipeline import NarrationPipeline
        
        pipeline = NarrationPipeline()
        assert pipeline.style == "悬疑"
        assert pipeline.max_scenes == 20
        
        pipeline2 = NarrationPipeline(
            style="幽默",
            max_scenes=15,
            cache_enabled=False
        )
        assert pipeline2.style == "幽默"
        assert pipeline2.max_scenes == 15
        assert pipeline2.analysis_chain.cache_enabled == False
    
    def test_pipeline_directories(self):
        """测试目录创建"""
        from core.pipeline import NarrationPipeline
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = NarrationPipeline(output_base_dir=tmpdir)
            
            expected_dirs = ['frames', 'scenes', 'scripts', 'voice', 'subtitles', 'videos']
            for dir_name in expected_dirs:
                dir_path = os.path.join(tmpdir, dir_name)
                assert os.path.exists(dir_path)
    
    def test_create_pipeline(self):
        """测试创建 Pipeline 便捷函数"""
        from core.pipeline import create_pipeline
        
        pipeline = create_pipeline(style="热血")
        assert pipeline.style == "热血"


class TestPrompts:
    """测试 Prompt 模板"""
    
    def test_style_descriptions(self):
        """测试风格描述"""
        from core.prompts import STYLE_DESCRIPTIONS
        
        assert "悬疑" in STYLE_DESCRIPTIONS
        assert "热血" in STYLE_DESCRIPTIONS
        assert "幽默" in STYLE_DESCRIPTIONS
        assert "温情" in STYLE_DESCRIPTIONS
        
        assert "悬念" in STYLE_DESCRIPTIONS["悬疑"]
        assert "激昂" in STYLE_DESCRIPTIONS["热血"]
    
    def test_video_analysis_prompt(self):
        """测试视频分析 Prompt"""
        from core.prompts import video_analysis_prompt
        
        assert video_analysis_prompt is not None
        # 验证可以格式化
        formatted = video_analysis_prompt.format(
            timestamp="01:23",
            image_url="data:image/png;base64,test"
        )
        assert "01:23" in formatted
    
    def test_script_generation_prompt(self):
        """测试文案生成 Prompt"""
        from core.prompts import script_generation_prompt
        
        assert script_generation_prompt is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
