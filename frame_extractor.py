import subprocess
import os
import json
from config import FRAMES_DIR, FRAME_INTERVAL
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

def extract_frames(video_path: str, output_dir: str = None, interval: int = FRAME_INTERVAL) -> tuple:
    
    return extract_frames_by_scenes(video_path, output_dir, interval,20)

from scene_detector import detect_scenes, filter_scenes

def extract_frames_by_scenes(video_path: str, output_dir: str = None, 
                              threshold: float = 30.0, max_scenes: int = 25) -> list:
    """基于场景检测提取关键帧"""
    if output_dir is None:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(FRAMES_DIR, video_name)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 检测场景
    scenes = detect_scenes(video_path, threshold=threshold)
    scenes = filter_scenes(scenes, min_duration=1.0, max_scenes=max_scenes)
    
    # 2. 为每个场景提取中心帧
    frames = []
    for i, scene in enumerate(scenes):
        timestamp = scene['center']
        output_path = os.path.join(output_dir, f"scene_{i+1:04d}_{int(timestamp)}s.png")
        
        cmd = ["ffmpeg", "-ss", str(timestamp), "-i", video_path,
               "-vframes", "1", "-q:v", "2", output_path, "-y"]
        subprocess.run(cmd, check=True, capture_output=True)
        
        frames.append({
            'path': output_path,
            'timestamp': timestamp,
            'time_str': f"{int(timestamp//60):02d}:{int(timestamp%60):02d}",
            'scene_start': scene['start'],
            'scene_end': scene['end'],
            'scene_duration': scene['duration']
        })
    
    print(f"  提取 {len(frames)} 个场景关键帧")
    return frames, scenes

def extract_frames_interval(video_path: str, output_dir: str, interval: int) -> list:
    # 临时禁用场景检测
    print("  使用固定间隔抽帧...")
    if output_dir is None:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(FRAMES_DIR, video_name)
    
    os.makedirs(output_dir, exist_ok=True)

    pattern = os.path.join(output_dir, "frame_%04d.png")
    cmd = ["ffmpeg", "-i", video_path, "-vf", f"fps=1/{interval}", pattern, "-y"]
    
    print(f"  执行抽帧命令: {' '.join(cmd)}")
    
    # 使用 Popen 避免卡死
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    try:
        stdout, stderr = process.communicate(timeout=120)
        print(f"  FFmpeg 返回码: {process.returncode}")
        
        if process.returncode != 0:
            print(f"  FFmpeg 错误: {stderr.decode()[:500]}")
            return []
            
    except subprocess.TimeoutExpired:
        process.kill()
        print("  FFmpeg 抽帧超时（120秒）")
        return []
    
    # 获取生成的帧文件列表
    frames = []
    if os.path.exists(output_dir):
        frames = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) 
                        if f.endswith(".png")])
    
    print(f"  固定间隔抽帧完成，共 {len(frames)} 帧")
    return frames

def get_video_duration(video_path: str) -> float:
    """获取视频时长（秒）"""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
           "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def get_video_info(video_path: str) -> dict:
    """获取视频详细信息"""
    cmd = ["ffprobe", "-v", "error", "-show_entries", 
           "stream=width,height,codec_name,r_frame_rate,codec_type", 
           "-of", "json", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    return {
        "width": video_stream.get("width", 0),
        "height": video_stream.get("height", 0),
        "duration": get_video_duration(video_path),
        "codec": video_stream.get("codec_name", "unknown")
    }
