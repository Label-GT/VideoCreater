"""
视频合成服务模块
封装视频剪辑、音频合成、字幕添加等逻辑
"""
import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from config import AUDIO_CODEC, SUBTITLE_DIR, VIDEO_CODEC, VIDEO_DIR, VIDEO_FPS
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    ImageClip,
    concatenate_audioclips
)


class CompositionService:
    """视频合成服务类"""
    
    def __init__(
        self,
        video_fps: int = 24,
        video_codec: str = "libx264",
        audio_codec: str = "aac",
        subtitle_font: str = "SimHei",
        subtitle_font_size: int = 24
    ):
        """
        初始化
        
        Args:
            video_fps: 视频帧率
            video_codec: 视频编码
            audio_codec: 音频编码
            subtitle_font: 字幕字体
            subtitle_font_size: 字幕字号
        """
        self.video_fps = video_fps
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.subtitle_font = subtitle_font
        self.subtitle_font_size = subtitle_font_size
    
    def format_time(self, seconds: float) -> str:
        """
        格式化时间为 SRT 格式
        
        Args:
            seconds: 秒数
        
        Returns:
            SRT 时间格式字符串 (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def generate_srt(
        self,
        scripts: List[Dict[str, Any]],
        voice_durations: List[float],
        movie_name: str,
        subtitle_dir: str
    ) -> str:
        """
        生成 SRT 字幕文件
        
        Args:
            scripts: 文案列表
            voice_durations: 语音时长列表
            movie_name: 电影名称
            subtitle_dir: 字幕输出目录
        
        Returns:
            字幕文件路径
        """
        srt_content = ""
        current_time = 0.0
        
        for i, (script, duration) in enumerate(zip(scripts, voice_durations)):
            start_time = current_time
            end_time = current_time + duration
            
            srt_content += f"{i+1}\n"
            srt_content += f"{self.format_time(start_time)} --> {self.format_time(end_time)}\n"
            srt_content += f"{script['script']}\n\n"
            
            current_time = end_time
        
        os.makedirs(subtitle_dir, exist_ok=True)
        subtitle_path = os.path.join(subtitle_dir, f"{movie_name}.srt")
        subtitle_path = Path(subtitle_path).as_posix()
        
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        print(f"  字幕已保存：{subtitle_path}")
        return subtitle_path
    
    def add_subtitle_ffmpeg(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str
    ) -> str:
        """
        使用 FFmpeg 添加硬字幕
        
        Args:
            video_path: 输入视频路径
            subtitle_path: 字幕文件路径
            output_path: 输出视频路径
        
        Returns:
            输出视频路径
        """
        subtitle_path = Path(subtitle_path).as_posix()
        
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"subtitles={subtitle_path}:force_style='FontName={self.subtitle_font},FontSize={self.subtitle_font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1'",
            "-c:a", "copy",
            output_path, "-y"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "未知错误"
            print(f"  FFmpeg 字幕添加失败：{error_msg[:200]}")
            return video_path
        
        return output_path
    
    def compose_sync_video(
        self,
        video_path: str,
        scenes: List[Dict[str, Any]],
        scripts: List[Dict[str, Any]],
        voice_paths: List[str],
        voice_durations: List[float],
        movie_name: str,
        video_dir: str,
        subtitle_dir: str
    ) -> str:
        """
        合成最终视频（定格适配）
        
        Args:
            video_path: 原视频路径
            scenes: 场景列表
            scripts: 文案列表
            voice_paths: 语音文件路径列表
            voice_durations: 语音时长列表
            movie_name: 电影名称
            video_dir: 视频输出目录
            subtitle_dir: 字幕输出目录
        
        Returns:
            最终视频路径
        """
        print("  加载原视频...")
        video = VideoFileClip(video_path)
        video_clips = []
        audio_clips = []
        
        for i, (scene, script, voice_path, voice_duration) in enumerate(
            zip(scenes, scripts, voice_paths, voice_durations)
        ):
            scene_start = scene['start']
            scene_end = scene['end']
            scene_duration = scene_end - scene_start
            
            print(f"  处理场景 {i+1}: 原{scene_duration:.1f}s → 配音{voice_duration:.1f}s")
            
            if voice_duration <= scene_duration:
                # 配音短：裁剪场景
                scene_clip = video.subclipped(scene_start, scene_start + voice_duration)
            else:
                # 配音长：正常播放 + 定格最后一帧
                scene_clip = video.subclipped(scene_start, scene_end)
                last_frame = scene_clip.get_frame(scene_clip.duration - 0.04)
                freeze_duration = voice_duration - scene_duration
                freeze_clip = ImageClip(last_frame, duration=freeze_duration)
                scene_clip = concatenate_videoclips([scene_clip, freeze_clip])
                print(f"    定格 {freeze_duration:.1f}秒")
            
            video_clips.append(scene_clip)
            audio_clips.append(AudioFileClip(voice_path))
        
        print("  拼接视频片段...")
        final_video = concatenate_videoclips(video_clips)
        
        print("  拼接音频...")
        final_audio = concatenate_audioclips(audio_clips)
        final_video = final_video.with_audio(final_audio)
        
        # 输出无字幕版本
        os.makedirs(video_dir, exist_ok=True)
        temp_output = os.path.join(video_dir, f"{movie_name}_temp.mp4")
        temp_output = Path(temp_output).as_posix()
        
        final_video.write_videofile(
            temp_output,
            fps=self.video_fps,
            codec=self.video_codec,
            audio_codec=self.audio_codec
        )
        
        # 清理资源
        video.close()
        final_video.close()
        for clip in video_clips:
            clip.close()
        for audio in audio_clips:
            audio.close()
        
        # 生成字幕
        subtitle_path = self.generate_srt(
            scripts=scripts,
            voice_durations=voice_durations,
            movie_name=movie_name,
            subtitle_dir=subtitle_dir
        )
        
        # 添加字幕
        output_path = os.path.join(video_dir, f"{movie_name}_final.mp4")
        output_path = Path(output_path).as_posix()
        final_path = self.add_subtitle_ffmpeg(temp_output, subtitle_path, output_path)
        
        # 删除临时文件
        if os.path.exists(temp_output) and temp_output != final_path:
            os.remove(temp_output)
        
        print(f"  视频已保存：{final_path}")
        return final_path


# 便捷函数
def compose_sync_video(
    video_path: str,
    scenes: List[Dict[str, Any]],
    scripts: List[Dict[str, Any]],
    voice_paths: List[str],
    voice_durations: List[float],
    movie_name: str,
    video_dir: str = None,
    subtitle_dir: str = None
) -> str:
    """
    合成视频（便捷函数）
    
    Args:
        video_path: 原视频路径
        scenes: 场景列表
        scripts: 文案列表
        voice_paths: 语音文件路径列表
        voice_durations: 语音时长列表
        movie_name: 电影名称
        video_dir: 视频输出目录
        subtitle_dir: 字幕输出目录
    
    Returns:
        最终视频路径
    """
    service = CompositionService(
        video_fps=VIDEO_FPS,
        video_codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC
    )
    
    return service.compose_sync_video(
        video_path=video_path,
        scenes=scenes,
        scripts=scripts,
        voice_paths=voice_paths,
        voice_durations=voice_durations,
        movie_name=movie_name,
        video_dir=video_dir or VIDEO_DIR,
        subtitle_dir=subtitle_dir or SUBTITLE_DIR
    )
