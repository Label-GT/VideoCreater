"""
电影解说生成完整 Pipeline
整合所有 Chains 和 Services，提供统一的调用接口

使用示例：
    from config import SCENE_THRESHOLD, MAX_SCENES, MIN_SCENE_DURATION, TTS_VOICE
    from core.pipeline import NarrationPipeline
    
    # 使用 config 中的默认配置
    pipeline = NarrationPipeline(
        style="悬疑",
        scene_threshold=SCENE_THRESHOLD,
        max_scenes=MAX_SCENES,
        min_scene_duration=MIN_SCENE_DURATION,
        tts_voice=TTS_VOICE
    )
    
    # 或者使用自定义配置
    pipeline = NarrationPipeline(
        style="热血",
        scene_threshold=25.0,
        max_scenes=15,
        min_scene_duration=2.0,
        tts_voice="zh-CN-YunjianNeural"
    )
"""
import json
import os
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from core.chains import VideoAnalysisChain, ScriptGenerationChain
from services.video_service import VideoService
from services.audio_service import AudioService
from services.composition_service import CompositionService


class NarrationPipeline:
    """
    电影解说生成 Pipeline
    
    完整流程：
    1. 获取视频信息
    2. 场景检测
    3. 关键帧提取
    4. 画面内容分析（AI）
    5. 解说文案生成（AI）
    6. 语音合成
    7. 视频合成
    """
    
    def __init__(
        self,
        style: str = "悬疑",
        scene_threshold: float = 35.0,
        min_scene_duration: float = 1.0,
        max_scenes: int = 20,
        tts_voice: str = "zh-CN-YunxiNeural",
        output_base_dir: str = "./outputs",
        use_theme_context: bool = True,
        cache_enabled: bool = True
    ):
        """
        初始化 Pipeline
        
        Args:
            style: 解说风格
            scene_threshold: 场景检测阈值
            min_scene_duration: 最小场景时长
            max_scenes: 最大场景数
            tts_voice: TTS 语音音色
            output_base_dir: 输出基础目录
            use_theme_context: 是否使用主题上下文
            cache_enabled: 是否启用缓存
        """
        self.style = style
        self.max_scenes = max_scenes
        self.output_base_dir = output_base_dir
        
        # 初始化服务
        self.video_service = VideoService(
            scene_threshold=scene_threshold,
            min_scene_duration=min_scene_duration
        )
        self.audio_service = AudioService(voice=tts_voice)
        self.composition_service = CompositionService(
            video_fps=24,
            video_codec="libx264",
            audio_codec="aac"
        )
        
        # 初始化 Chains
        self.analysis_chain = VideoAnalysisChain(cache_enabled=cache_enabled)
        self.script_chain = ScriptGenerationChain(
            style=style,
            use_theme_context=use_theme_context
        )
        
        # 设置输出目录
        self._setup_directories()
    
    def _setup_directories(self):
        """设置输出目录"""
        self.dirs = {
            'frames': os.path.join(self.output_base_dir, "frames"),
            'scenes': os.path.join(self.output_base_dir, "scenes"),
            'scripts': os.path.join(self.output_base_dir, "scripts"),
            'voice': os.path.join(self.output_base_dir, "voice"),
            'subtitles': os.path.join(self.output_base_dir, "subtitles"),
            'videos': os.path.join(self.output_base_dir, "videos"),
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
    
    def execute(
        self,
        video_path: str,
        movie_name: str = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        bgm_path: str = None,
        bgm_volume: float = 0.3
    ) -> Dict[str, Any]:
        """
        执行完整的解说视频生成流程
        
        Args:
            video_path: 输入视频路径
            movie_name: 电影名称（可选，默认使用文件名）
            progress_callback: 进度回调函数 (current_step, total_steps, message)
            bgm_path: 背景音乐文件路径（可选）
            bgm_volume: BGM 音量比例（0-1，默认 0.3）
        
        Returns:
            生成结果，包含输出路径、统计信息等
        """
        if movie_name is None:
            movie_name = Path(video_path).stem
        
        total_steps = 7
        
        try:
            # Step 1: 获取视频信息
            if progress_callback:
                progress_callback(1, total_steps, "获取视频信息...")
            video_info = self.video_service.get_video_info(video_path)
            print(f"视频时长：{video_info['duration']:.2f}秒")
            print(f"分辨率：{video_info['width']}x{video_info['height']}")
            
            # Step 2: 场景检测
            if progress_callback:
                progress_callback(2, total_steps, "检测场景...")
            scenes = self.video_service.detect_scenes(
                video_path=video_path,
                movie_name=movie_name,
                scenes_dir=self.dirs['scenes'],
                max_scenes=self.max_scenes
            )
            
            # Step 3: 提取关键帧
            if progress_callback:
                progress_callback(3, total_steps, "提取关键帧...")
            frames = self.video_service.extract_keyframes(
                video_path=video_path,
                scenes=scenes,
                movie_name=movie_name,
                frames_dir=self.dirs['frames']
            )
            
            # Step 4: 分析画面内容
            if progress_callback:
                progress_callback(4, total_steps, "分析画面内容...")
            analyses = self.analysis_chain.analyze(
                frames=frames,
                movie_name=movie_name,
                scripts_dir=self.dirs['scripts'],
                progress_callback=progress_callback
            )
            
            # Step 5: 生成解说文案
            if progress_callback:
                progress_callback(5, total_steps, "生成解说文案...")
            scripts = self.script_chain.generate(
                analyses=analyses,
                scenes=scenes,
                movie_name=movie_name,
                scripts_dir=self.dirs['scripts'],
                progress_callback=progress_callback
            )
            
            # Step 6: 语音合成
            if progress_callback:
                progress_callback(6, total_steps, "语音合成...")
            voice_paths, voice_durations = self.audio_service.process_tts(
                scripts=scripts,
                movie_name=movie_name,
                voice_dir=self.dirs['voice']
            )
            
            # Step 7: 合成视频
            if progress_callback:
                progress_callback(7, total_steps, "合成视频...")
            output_path = self.composition_service.compose_sync_video(
                video_path=video_path,
                scenes=scenes,
                scripts=scripts,
                voice_paths=voice_paths,
                voice_durations=voice_durations,
                movie_name=movie_name,
                video_dir=self.dirs['videos'],
                subtitle_dir=self.dirs['subtitles'],
                bgm_path=bgm_path,
                bgm_volume=bgm_volume
            )
            
            # 完成
            if progress_callback:
                progress_callback(total_steps, total_steps, "完成！")
            
            total_duration = sum(voice_durations)
            
            return {
                'status': 'success',
                'output_path': output_path,
                'movie_name': movie_name,
                'scene_count': len(scenes),
                'total_duration': total_duration,
                'video_info': video_info
            }
            
        except Exception as e:
            error_msg = traceback.format_exc()
            print(f"处理失败：{error_msg}")
            
            return {
                'status': 'failed',
                'error': str(e),
                'traceback': error_msg
            }
    
    def execute_async(
        self,
        video_path: str,
        movie_name: str = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ):
        """
        异步执行（用于 Celery 等任务队列）
        
        Args:
            video_path: 输入视频路径
            movie_name: 电影名称
            progress_callback: 进度回调
        
        Returns:
            同 execute()
        """
        # 目前同步执行，未来可集成 Celery
        return self.execute(video_path, movie_name, progress_callback)


# 便捷函数
def create_pipeline(
    style: str = "悬疑",
    **kwargs
) -> NarrationPipeline:
    """
    创建 Pipeline 实例的便捷函数
    
    Args:
        style: 解说风格
        **kwargs: 其他参数
    
    Returns:
        NarrationPipeline 实例
    """
    return NarrationPipeline(style=style, **kwargs)


def generate_narration_video(
    video_path: str,
    style: str = "悬疑",
    movie_name: str = None,
    scene_threshold: float = 35.0,
    max_scenes: int = 20,
    min_scene_duration: float = 1.0,
    tts_voice: str = "zh-CN-YunxiNeural",
    bgm_path: str = None,
    bgm_volume: float = 0.3,
    progress_callback=None
) -> Dict[str, Any]:
    """
    一键生成解说视频的便捷函数
    
    Args:
        video_path: 输入视频路径
        style: 解说风格
        movie_name: 电影名称
        scene_threshold: 场景检测阈值
        max_scenes: 最大场景数
        min_scene_duration: 最小场景时长
        tts_voice: TTS 语音音色
        bgm_path: 背景音乐文件路径（可选）
        bgm_volume: BGM 音量比例（0-1，默认 0.3）
        progress_callback: 进度回调
    
    Returns:
        生成结果
    """
    pipeline = create_pipeline(
        style=style,
        scene_threshold=scene_threshold,
        max_scenes=max_scenes,
        min_scene_duration=min_scene_duration,
        tts_voice=tts_voice
    )
    return pipeline.execute(
        video_path, 
        movie_name, 
        progress_callback,
        bgm_path=bgm_path,
        bgm_volume=bgm_volume
    )
