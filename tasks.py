# tasks.py
"""
Celery 异步任务模块
使用重构后的 Pipeline
"""
import os
import traceback
from pathlib import Path

from celery import Celery

from config import MAX_SCENES, MIN_SCENE_DURATION, SCENE_THRESHOLD, TTS_VOICE
from core.pipeline import NarrationPipeline

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


@app.task(bind=True)
def generate_narration(self, video_path: str, style: str, movie_name: str = None):
    """
    异步生成解说视频
    
    Args:
        video_path: 视频文件路径
        style: 解说风格
        movie_name: 电影名称（可选）
    
    Returns:
        处理结果字典
    """
    if movie_name is None:
        movie_name = Path(video_path).stem
    
    def progress_callback(current, total, message):
        """进度回调"""
        percent = int(current / total * 100)
        self.update_state(
            state='PROGRESS',
            meta={'progress': percent, 'stage': message}
        )
        print(f"[{percent}%] {message}")
    
    try:
        # 创建 Pipeline 实例（使用 config 中的配置）
        pipeline = NarrationPipeline(
            style=style,
            scene_threshold=SCENE_THRESHOLD,
            max_scenes=MAX_SCENES,
            min_scene_duration=MIN_SCENE_DURATION,
            tts_voice=TTS_VOICE
        )
        
        # 执行 Pipeline
        result = pipeline.execute(
            video_path=video_path,
            movie_name=movie_name,
            progress_callback=progress_callback
        )
        
        return result
        
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"处理失败：{error_msg}")
        return {
            'status': 'failed',
            'error': str(e),
            'traceback': error_msg
        }
