import subprocess
import os
import json
from config import FRAMES_DIR, FRAME_INTERVAL
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

def extract_frames(video_path: str, output_dir: str = None, interval: int = FRAME_INTERVAL) -> list:
    # 临时禁用场景检测
    print("  使用固定间隔抽帧...")
    return extract_frames_interval(video_path, output_dir, interval)

def extract_frames_SCENE(video_path: str, output_dir: str = None, 
                   interval: int = FRAME_INTERVAL, max_frames: int = 30) -> list:
    """
    基于场景检测提取关键帧，但限制最大帧数
    max_frames: 最多提取多少帧（默认30）
    """
    if output_dir is None:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(FRAMES_DIR, video_name)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 检测场景
    print("  正在检测场景切换...")
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=40.0))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()
    
    print(f"  检测到 {len(scene_list)} 个场景")
    
    if not scene_list:
        return extract_frames_interval(video_path, output_dir, interval)
    
    # 2. 如果场景数超过 max_frames，均匀采样
    if len(scene_list) > max_frames:
        print(f"  场景过多，均匀采样至 {max_frames} 个关键帧")
        step = len(scene_list) / max_frames
        indices = [int(i * step) for i in range(max_frames)]
        sampled_scenes = [scene_list[i] for i in indices]
    else:
        sampled_scenes = scene_list
    
    # 3. 提取帧
    frame_paths = []
    for i, scene in enumerate(sampled_scenes):
        center_time = (scene[0].get_seconds() + scene[1].get_seconds()) / 2
        output_path = os.path.join(output_dir, f"frame_{i+1:04d}_{int(center_time)}s.png")
        
        cmd = ["ffmpeg", "-ss", str(center_time), "-i", video_path,
               "-vframes", "1", "-q:v", "2", output_path, "-y"]
        subprocess.run(cmd, check=True, capture_output=True)
        frame_paths.append(output_path)
    
    print(f"  共提取 {len(frame_paths)} 个关键帧")
    return frame_paths

def extract_frames_interval(video_path: str, output_dir: str, interval: int) -> list:
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

def run_ffmpeg(cmd, timeout=60):
    """运行 FFmpeg 命令，避免卡死"""
    print(f"执行: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        print(f"返回码: {process.returncode}")
        return process.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        print("命令超时")
        return -1, b'', b'Timeout'