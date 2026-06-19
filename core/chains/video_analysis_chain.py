"""
视频分析 Chain 模块
使用 LangChain 封装视觉分析流程
"""
import base64
import hashlib
import io
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from core.models import zhipu_vision_llm
from core.prompts import video_analysis_prompt
from PIL import Image


class ProgressCallback(BaseCallbackHandler):
    """进度追踪 Callback"""
    
    def __init__(self, progress_callback=None):
        super().__init__()
        self.progress_callback = progress_callback
        self.current_step = 0
        self.total_steps = 0
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        """Chain 开始时调用"""
        if self.progress_callback:
            self.progress_callback(0, "开始分析...")
    
    def on_chain_end(self, outputs, **kwargs):
        """Chain 结束时调用"""
        if self.progress_callback:
            self.progress_callback(100, "分析完成")


def encode_image(image_path: str, max_size: int = 512) -> str:
    """
    将图片编码为 base64（带压缩）
    
    Args:
        image_path: 图片路径
        max_size: 最大边长（像素），默认 512
    
    Returns:
        base64 编码的图片数据
    """
    # 打开图片
    img = Image.open(image_path)
    
    # 计算缩放比例
    width, height = img.size
    if max(width, height) > max_size:
        ratio = max_size / max(width, height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 压缩为 JPEG 格式
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    
    # 编码为 base64
    return base64.b64encode(buffer.getvalue()).decode()


def create_video_analysis_chain(callback_handler: Optional[BaseCallbackHandler] = None):
    """
    创建视频分析 Chain
    
    Returns:
        可执行的 Chain 对象
    """
    # 构建处理图片的 RunnableLambda
    def process_image(frame: Dict[str, Any]) -> Dict[str, Any]:
        """处理单帧图片（压缩后）"""
        base64_image = encode_image(frame['path'], max_size=512)
        return {
            **frame,
            'image_url': f"data:image/jpeg;base64,{base64_image}"
        }
    
    # 构建 Chain
    chain = (
        RunnablePassthrough.assign(image_url=RunnableLambda(process_image))
        | video_analysis_prompt
        | zhipu_vision_llm
        | StrOutputParser()
    )
    
    return chain


def analyze_frames(
    frames: List[Dict[str, Any]],
    movie_name: str,
    scripts_dir: str,
    max_retries: int = 6,
    retry_delay: int = 2,
    progress_callback=None
) -> List[Dict[str, Any]]:
    """
    分析所有场景画面
    
    Args:
        frames: 关键帧列表，每项包含 path, scene_index, timestamp, time_str
        movie_name: 电影名称
        scripts_dir: 脚本输出目录
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        progress_callback: 进度回调函数 (current, total, message)
    
    Returns:
        分析结果列表
    """
    analyses = []
    chain = create_video_analysis_chain()
    
    total_frames = len(frames)
    
    for i, frame in enumerate(frames):
        if progress_callback:
            progress_callback(i + 1, total_frames, f"分析场景 {i+1}/{total_frames}: {frame['time_str']}")
        
        analysis_result = None
        
        for attempt in range(max_retries):
            try:
                # 执行 Chain
                description = chain.invoke(frame)
                
                analysis_result = {
                    'scene_index': frame['scene_index'],
                    'timestamp': frame['timestamp'],
                    'time_str': frame['time_str'],
                    'description': description.strip()
                }
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * retry_delay
                    print(f"    限流或错误，{wait_time}秒后重试... (尝试 {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"    分析失败：{e}")
                    analysis_result = {
                        'scene_index': frame['scene_index'],
                        'timestamp': frame['timestamp'],
                        'time_str': frame['time_str'],
                        'description': "画面分析失败"
                    }
        
        analyses.append(analysis_result)
        
        # 避免限流
        if i < total_frames - 1:
            time.sleep(1)
    
    # 保存分析结果
    os.makedirs(scripts_dir, exist_ok=True)
    analyses_path = os.path.join(scripts_dir, f"{movie_name}_analyses.json")
    with open(analyses_path, 'w', encoding='utf-8') as f:
        json.dump(analyses, f, indent=2, ensure_ascii=False)
    
    print(f"分析结果已保存：{analyses_path}")
    
    return analyses


class VideoAnalysisChain:
    """
    视频分析 Chain 封装类
    提供更高级的接口，支持批量处理、缓存等功能
    """
    
    def __init__(self, cache_enabled: bool = True, cache_dir: str = None):
        self.cache_enabled = cache_enabled
        self.cache_dir = cache_dir or "./cache/video_analysis"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, frame_path: str) -> str:
        """生成缓存键"""
        with open(frame_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """从缓存获取结果"""
        if not self.cache_enabled:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    
    def _save_to_cache(self, cache_key: str, description: str):
        """保存结果到缓存"""
        if not self.cache_enabled:
            return
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(description)
    
    def analyze(
        self,
        frames: List[Dict[str, Any]],
        movie_name: str,
        scripts_dir: str,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        分析视频帧
        
        Args:
            frames: 关键帧列表
            movie_name: 电影名称
            scripts_dir: 输出目录
            progress_callback: 进度回调
        
        Returns:
            分析结果列表
        """
        return analyze_frames(
            frames=frames,
            movie_name=movie_name,
            scripts_dir=scripts_dir,
            progress_callback=progress_callback
        )
