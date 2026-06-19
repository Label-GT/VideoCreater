"""
音频处理服务模块
封装 TTS 语音合成和背景音乐处理逻辑
"""
import asyncio
import json
import os
from typing import List, Tuple, Dict, Any

import edge_tts
from pydub import AudioSegment
from moviepy import AudioFileClip, concatenate_audioclips, CompositeAudioClip, VideoFileClip


class AudioService:
    """音频处理服务类"""
    
    def __init__(self, voice: str = "zh-CN-YunxiNeural"):
        """
        初始化
        
        Args:
            voice: TTS 语音音色
        """
        self.voice = voice
    
    async def text_to_speech_async(
        self,
        text: str,
        output_path: str,
        voice: str = None
    ):
        """
        异步文本转语音
        
        Args:
            text: 文本内容
            output_path: 输出路径
            voice: 语音音色（可选，默认使用实例配置）
        """
        voice = voice or self.voice
        communicate = edge_tts.Communicate(text, voice)
        
        with open(output_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
    
    def text_to_speech(self, text: str, output_path: str, voice: str = None):
        """
        同步文本转语音
        
        Args:
            text: 文本内容
            output_path: 输出路径
            voice: 语音音色
        """
        asyncio.run(self.text_to_speech_async(text, output_path, voice))
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        获取音频时长（秒）
        
        Args:
            audio_path: 音频文件路径
        
        Returns:
            时长（秒）
        """
        audio = AudioSegment.from_mp3(audio_path)
        return len(audio) / 1000.0
    
    def process_tts(
        self,
        scripts: List[Dict[str, Any]],
        movie_name: str,
        voice_dir: str
    ) -> Tuple[List[str], List[float]]:
        """
        为所有场景生成配音
        
        Args:
            scripts: 文案列表
            movie_name: 电影名称
            voice_dir: 语音文件保存目录
        
        Returns:
            (语音文件路径列表，语音时长列表)
        """
        voice_paths = []
        voice_durations = []
        
        os.makedirs(voice_dir, exist_ok=True)
        
        for script in scripts:
            voice_path = os.path.join(
                voice_dir,
                f"{movie_name}_scene_{script['scene_index']:04d}.mp3"
            )
            print(f"  合成语音：{voice_path}")
            
            self.text_to_speech(script['script'], voice_path)
            
            duration = self.get_audio_duration(voice_path)
            voice_paths.append(voice_path)
            voice_durations.append(duration)
            
            # 更新 script 信息
            script['voice_duration'] = duration
            script['voice_path'] = voice_path
            
            print(f"    时长：{duration:.1f}秒")
        
        # 保存更新后的 scripts（包含配音信息）
        scripts_path = os.path.join(voice_dir, f"{movie_name}_voice_info.json")
        with open(scripts_path, 'w', encoding='utf-8') as f:
            json.dump(scripts, f, indent=2, ensure_ascii=False)
        
        return voice_paths, voice_durations
    
    def add_background_music(
        self,
        video_path: str,
        bgm_path: str,
        bgm_volume: float = 0.3,
        fade_duration: float = 2.0
    ) -> str:
        """
        为视频添加背景音乐
        
        Args:
            video_path: 输入视频路径（已含配音）
            bgm_path: 背景音乐文件路径
            bgm_volume: BGM 音量比例（0-1，默认 0.3）
            fade_duration: 淡出时长（秒）
        
        Returns:
            输出视频路径（含 BGM）
        """
        print(f"  添加背景音乐：{os.path.basename(bgm_path)}，音量：{bgm_volume*100:.0f}%")
        
        try:
            # 1. 加载视频和 BGM
            video = VideoFileClip(video_path)
            bgm = AudioFileClip(bgm_path)
            
            video_duration = video.duration
            bgm_duration = bgm.duration
            
            # 2. 处理 BGM 时长
            if bgm_duration < video_duration:
                # BGM 短：循环播放
                print(f"    BGM 时长 ({bgm_duration:.1f}s) < 视频时长 ({video_duration:.1f}s)，循环播放")
                bgm = self._loop_audio(bgm, video_duration)
            else:
                # BGM 长：裁剪 + 淡出
                print(f"    BGM 时长 ({bgm_duration:.1f}s) > 视频时长 ({video_duration:.1f}s)，裁剪并淡出")
                bgm = bgm.subclipped(0, video_duration)
                bgm = bgm.audio_fadeout(fade_duration)
            
            # 3. 调节音量（在混合之前）
            # MoviePy 2.x 使用 with_volume_scaled 方法
            bgm = bgm.with_volume_scaled(bgm_volume)
            
            # 4. 混合音频（视频原音频 + BGM）
            # 注意：CompositeAudioClip 会自动混合所有音轨
            final_audio = CompositeAudioClip([video.audio, bgm])
            video = video.with_audio(final_audio)
            
            # 5. 输出
            output_path = video_path.replace('.mp4', '_with_bgm.mp4')
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                logger=None  # 静音模式
            )
            
            # 6. 清理资源
            video.close()
            bgm.close()
            
            print(f"  视频已保存（含 BGM）：{output_path}")
            return output_path
            
        except Exception as e:
            print(f"  警告：BGM 处理失败：{e}，返回原始视频")
            return video_path
    
    def _loop_audio(self, audio, target_duration):
        """
        循环音频直到达到目标时长
        
        Args:
            audio: AudioFileClip 对象
            target_duration: 目标时长（秒）
        
        Returns:
            循环后的 AudioFileClip
        """
        loops_needed = int(target_duration / audio.duration) + 1
        clips = [audio] * loops_needed
        looped = concatenate_audioclips(clips)
        return looped.subclipped(0, target_duration)


# 便捷函数
def process_tts(
    scripts: List[Dict[str, Any]],
    movie_name: str,
    voice_dir: str,
    voice: str = "zh-CN-YunxiNeural"
) -> Tuple[List[str], List[float]]:
    """处理 TTS（便捷函数）"""
    service = AudioService(voice)
    return service.process_tts(scripts, movie_name, voice_dir)
