"""
音频处理服务模块
封装 TTS 语音合成逻辑
"""
import asyncio
import json
import os
from typing import List, Tuple, Dict, Any

import edge_tts
from pydub import AudioSegment


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
