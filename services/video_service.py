"""
视频处理服务模块
封装场景检测、关键帧提取等非 AI 逻辑
"""
import os
import subprocess
import json
from typing import List, Dict, Any
from pathlib import Path

from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector


class VideoService:
    """视频处理服务类"""
    
    def __init__(self, scene_threshold: float = 35.0, min_scene_duration: float = 1.0):
        """
        初始化
        
        Args:
            scene_threshold: 场景检测阈值
            min_scene_duration: 最小场景时长（秒）
        """
        self.scene_threshold = scene_threshold
        self.min_scene_duration = min_scene_duration
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            包含视频信息的字典
        """
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name,r_frame_rate",
            "-of", "json", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        
        # 获取时长
        duration_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
        duration = float(duration_result.stdout.strip())
        
        # 解析帧率
        r_frame_rate = stream.get("r_frame_rate", "0/1")
        if "/" in r_frame_rate:
            num, den = r_frame_rate.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 0
        else:
            fps = float(r_frame_rate)
        
        return {
            "width": stream.get("width", 0),
            "height": stream.get("height", 0),
            "codec": stream.get("codec_name", "unknown"),
            "fps": fps,
            "duration": duration
        }
    
    def detect_scenes(
        self,
        video_path: str,
        movie_name: str,
        scenes_dir: str,
        max_scenes: int = 20
    ) -> List[Dict[str, Any]]:
        """
        检测场景并保存
        
        Args:
            video_path: 视频路径
            movie_name: 电影名称
            scenes_dir: 场景信息保存目录
            max_scenes: 最大场景数
        
        Returns:
            场景列表
        """
        print("  正在检测场景切换...")
        
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=self.scene_threshold))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()
        
        scenes = []
        for scene in scene_list:
            start = scene[0].get_seconds()
            end = scene[1].get_seconds()
            duration = end - start
            if duration >= self.min_scene_duration:
                scenes.append({
                    'index': len(scenes),
                    'start': start,
                    'end': end,
                    'duration': duration,
                    'center': (start + end) / 2
                })
        
        print(f"  检测到 {len(scenes)} 个场景")
        
        # 限制场景数量
        if len(scenes) > max_scenes:
            print(f"  场景过多，均匀采样至 {max_scenes} 个")
            step = len(scenes) / max_scenes
            scenes = [scenes[int(i * step)] for i in range(max_scenes)]
        
        # 保存场景信息
        os.makedirs(scenes_dir, exist_ok=True)
        scenes_path = os.path.join(scenes_dir, f"{movie_name}_scenes.json")
        with open(scenes_path, 'w', encoding='utf-8') as f:
            json.dump(scenes, f, indent=2, ensure_ascii=False)
        print(f"  场景信息已保存：{scenes_path}")
        
        return scenes
    
    def extract_keyframes(
        self,
        video_path: str,
        scenes: List[Dict[str, Any]],
        movie_name: str,
        frames_dir: str
    ) -> List[Dict[str, Any]]:
        """
        提取关键帧
        
        Args:
            video_path: 视频路径
            scenes: 场景列表
            movie_name: 电影名称
            frames_dir: 关键帧保存目录
        
        Returns:
            关键帧列表
        """
        frames = []
        os.makedirs(frames_dir, exist_ok=True)
        
        for scene in scenes:
            timestamp = scene['center']
            output_path = os.path.join(frames_dir, f"{movie_name}_scene_{scene['index']:04d}.png")
            
            cmd = [
                "ffmpeg", "-ss", str(timestamp), "-i", video_path,
                "-vframes", "1", "-q:v", "2", output_path, "-y"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            frames.append({
                'path': output_path,
                'scene_index': scene['index'],
                'timestamp': timestamp,
                'time_str': f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"
            })
            
            print(f"  提取帧 {scene['index']+1}: {output_path}")
        
        print(f"  共提取 {len(frames)} 个关键帧")
        return frames


# 便捷函数
def get_video_info(video_path: str) -> Dict[str, Any]:
    """获取视频信息（便捷函数）"""
    service = VideoService()
    return service.get_video_info(video_path)


def detect_scenes(
    video_path: str,
    movie_name: str,
    scenes_dir: str,
    **kwargs
) -> List[Dict[str, Any]]:
    """检测场景（便捷函数）"""
    service = VideoService()
    return service.detect_scenes(video_path, movie_name, scenes_dir, **kwargs)


def extract_keyframes(
    video_path: str,
    scenes: List[Dict[str, Any]],
    movie_name: str,
    frames_dir: str
) -> List[Dict[str, Any]]:
    """提取关键帧（便捷函数）"""
    service = VideoService()
    return service.extract_keyframes(video_path, scenes, movie_name, frames_dir)
