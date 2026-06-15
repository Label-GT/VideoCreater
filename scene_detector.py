import subprocess
import os
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

def detect_scenes(video_path: str, threshold: float = 30.0, min_scene_len: int = 30) -> list:
    """
    检测视频场景切换点
    返回场景列表: [(start_time, end_time), ...]
    """
    print(f"  正在检测场景切换（阈值={threshold}）...")
    
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=40.0, min_scene_len=min_scene_len))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()
    
    scenes = []
    for scene in scene_list:
        start = scene[0].get_seconds()
        end = scene[1].get_seconds()
        duration = end - start
        scenes.append({
            'start': start,
            'end': end,
            'duration': duration,
            'center': (start + end) / 2
        })
    
    print(f"  检测到 {len(scenes)} 个场景")
    return scenes

def filter_scenes(scenes: list, min_duration: float = 1.0, max_scenes: int = 30) -> list:
    """过滤太短的场景，限制数量"""
    filtered = [s for s in scenes if s['duration'] >= min_duration]
    
    if len(filtered) > max_scenes:
        # 均匀采样
        step = len(filtered) / max_scenes
        filtered = [filtered[int(i * step)] for i in range(max_scenes)]
    
    return filtered