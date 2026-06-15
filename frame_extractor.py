import os
import subprocess
import json
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from config import FRAMES_DIR, SCENES_DIR, SCENE_THRESHOLD, MAX_SCENES, MIN_SCENE_DURATION

def get_video_info(video_path: str) -> dict:
    """获取视频信息"""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,codec_name,r_frame_rate",
           "-of", "json", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    stream = data.get("streams", [{}])[0]
    
    # 获取时长
    duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", video_path]
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

def detect_scenes(video_path: str, movie_name: str) -> list:
    """检测场景并保存到文件"""
    print("  正在检测场景切换...")
    
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=SCENE_THRESHOLD))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()
    
    scenes = []
    for scene in scene_list:
        start = scene[0].get_seconds()
        end = scene[1].get_seconds()
        duration = end - start
        if duration >= MIN_SCENE_DURATION:
            scenes.append({
                'index': len(scenes),
                'start': start,
                'end': end,
                'duration': duration,
                'center': (start + end) / 2
            })
    
    print(f"  检测到 {len(scenes)} 个场景")
    
    # 限制场景数量
    if len(scenes) > MAX_SCENES:
        print(f"  场景过多，均匀采样至 {MAX_SCENES} 个")
        step = len(scenes) / MAX_SCENES
        scenes = [scenes[int(i * step)] for i in range(MAX_SCENES)]
    
    # 保存场景信息
    scenes_path = os.path.join(SCENES_DIR, f"{movie_name}_scenes.json")
    with open(scenes_path, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)
    print(f"  场景信息已保存: {scenes_path}")
    
    return scenes

def extract_keyframes(video_path: str, scenes: list, movie_name: str) -> list:
    """提取每个场景的关键帧"""
    frames = []
    
    for scene in scenes:
        timestamp = scene['center']
        output_path = os.path.join(FRAMES_DIR, f"{movie_name}_scene_{scene['index']:04d}.png")
        
        cmd = ["ffmpeg", "-ss", str(timestamp), "-i", video_path,
               "-vframes", "1", "-q:v", "2", output_path, "-y"]
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