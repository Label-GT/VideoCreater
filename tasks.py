# tasks.py
import os
import time
import subprocess
from pathlib import Path
from celery import Celery

# Celery 配置
REDIS_URL = 'redis://127.0.0.1:6379'
print(f"PATH: {os.environ.get('PATH', '')[:5000]}")

app = Celery(
    'movie_tasks',
    broker=REDIS_URL + '/0',
    backend=REDIS_URL + '/1',
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
    task_time_limit=1800,      # 任务最大执行时间 30 分钟
    task_soft_time_limit=1500, # 软超时 25 分钟
)

# 导入处理模块
from frame_extractor import get_video_info, extract_frames
from video_analyzer import analyze_frames_batch
from script_generator import generate_script, save_script
from tts_generator import process_tts
from video_composer import compose_video

@app.task(bind=True)
def generate_narration(self, video_path: str, style: str, movie_name: str = None):
    
    """
    异步生成解说视频
    """
    if movie_name is None:
        movie_name = Path(video_path).stem
    
    try:
        # 1. 获取视频信息 (5%)
        self.update_state(state='PROGRESS', meta={'progress': 5, 'stage': '获取视频信息'})
        video_info = get_video_info(video_path)
        print(f"视频时长: {video_info['duration']:.2f}秒")
        print(f"分辨率: {video_info['width']}x{video_info['height']}")
        
        # 2. 提取关键帧 (10%)
        self.update_state(state='PROGRESS', meta={'progress': 10, 'stage': '提取关键帧'})
        frames = extract_frames(video_path, interval=30)
        print(f"共提取 {len(frames)} 个关键帧")
        
        # 3. 分析画面内容 (20-60%)
        self.update_state(state='PROGRESS', meta={'progress': 20, 'stage': '分析画面内容'})
        descriptions = analyze_frames_batch(frames, sample_rate=0.2)
        
        # 4. 生成解说文案 (60-70%)
        self.update_state(state='PROGRESS', meta={'progress': 60, 'stage': '生成解说文案'})
        script = generate_script(movie_name, descriptions, style)
        script_path = save_script(script, movie_name)
        print(f"文案已保存: {script_path}")
        
        # 5. 语音合成 + 字幕 (70-85%)
        self.update_state(state='PROGRESS', meta={'progress': 70, 'stage': '语音合成'})
        voice_path, subtitle_path = process_tts(script, movie_name)
        
        # 6. 合成最终视频 (85-100%)
        self.update_state(state='PROGRESS', meta={'progress': 85, 'stage': '合成视频'})
        output_path = compose_video(video_path, voice_path, subtitle_path, movie_name)
        
        # 完成
        self.update_state(state='PROGRESS', meta={'progress': 100, 'stage': '完成'})
        
        return {
            'status': 'completed',
            'output_path': output_path,
            'movie_name': movie_name,
            'duration': video_info['duration']
        }
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"处理失败: {error_msg}")
        return {
            'status': 'failed',
            'error': str(e),
            'traceback': error_msg
        }