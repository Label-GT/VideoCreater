# tasks.py
import os
import time
from pathlib import Path
from celery import Celery

# 创建 Celery 应用（连接 Docker 中的 Redis）
app = Celery(
    'movie_tasks',
    broker='redis://127.0.0.1:6379/0',      # Redis 在 Docker 容器中
    backend='redis://127.0.0.1:6379/1'
)

# Windows 兼容配置
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    worker_pool='eventlet',  # Windows 必须用 eventlet
)

@app.task(bind=True)
def test_task(self, message: str):
    """测试任务"""
    self.update_state(state='PROGRESS', meta={'progress': 0, 'stage': '开始'})
    time.sleep(2)
    self.update_state(state='PROGRESS', meta={'progress': 50, 'stage': '处理中'})
    time.sleep(2)
    return f"完成: {message}"