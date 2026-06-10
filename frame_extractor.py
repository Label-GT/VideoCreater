import subprocess
import os
from config import FRAMES_DIR, AUDIO_DIR, FRAME_INTERVAL

def extract_audio(video_path: str, output_path: str = None) -> str:
    """提取视频中的音频"""
    if output_path is None:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(AUDIO_DIR, f"{video_name}_audio.mp3")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cmd = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", output_path, "-y"]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def extract_frames(video_path: str, output_dir: str = None, interval: int = FRAME_INTERVAL) -> list:
    """提取视频关键帧，返回所有帧的路径列表"""
    if output_dir is None:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(FRAMES_DIR, video_name)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 先获取视频总时长，用于生成帧文件名
    duration = get_video_duration(video_path)
    
    # 提取帧
    pattern = os.path.join(output_dir, "frame_%04d.png")
    cmd = ["ffmpeg", "-i", video_path, "-vf", f"fps=1/{interval}", pattern, "-y"]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # 返回所有帧路径列表
    frames = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".png")])
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
           "stream=width,height,codec_name,r_frame_rate", 
           "-of", "json", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    import json
    data = json.loads(result.stdout)
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    return {
        "width": video_stream.get("width", 0),
        "height": video_stream.get("height", 0),
        "duration": get_video_duration(video_path),
        "codec": video_stream.get("codec_name", "unknown")
    }
