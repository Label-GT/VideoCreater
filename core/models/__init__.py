"""
Models 模块初始化
"""
from core.models import model_config

from core.models.model_config import (
    # 配置
    ZHIPU_API_KEY,
    ZHIPU_BASE_URL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    
    # 工厂函数
    create_zhipu_llm,
    create_deepseek_llm,
    
    # 默认实例
    zhipu_vision_llm,
    deepseek_text_llm
)

__all__ = [
    # Config
    'ZHIPU_API_KEY',
    'ZHIPU_BASE_URL',
    'DEEPSEEK_API_KEY',
    'DEEPSEEK_BASE_URL',
    
    # Factory Functions
    'create_zhipu_llm',
    'create_deepseek_llm',
    
    # Default Instances
    'zhipu_vision_llm',
    'deepseek_text_llm',
]
