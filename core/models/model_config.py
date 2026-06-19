"""
LangChain 配置模块
初始化 LLM 模型、Embedding 等组件
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

load_dotenv()

# API 配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "https://api.zhipu.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


def create_zhipu_llm(
    model_name: str = "glm-4.6v-flash",
    temperature: float = 0.7,
    max_tokens: int = 500,
    **kwargs
) -> BaseChatModel:
    """
    创建智谱 AI 视觉模型实例
    
    Args:
        model_name: 模型名称
        temperature: 温度参数，控制随机性
        max_tokens: 最大生成 token 数
        **kwargs: 其他参数
    
    Returns:
        ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_BASE_URL,
        **kwargs
    )


def create_deepseek_llm(
    model_name: str = "deepseek-v4-flash",
    temperature: float = 0.8,
    max_tokens: int = 500,
    **kwargs
) -> BaseChatModel:
    """
    创建 DeepSeek 文本模型实例
    
    Args:
        model_name: 模型名称
        temperature: 温度参数，控制随机性
        max_tokens: 最大生成 token 数
        **kwargs: 其他参数
    
    Returns:
        ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        **kwargs
    )


# 默认模型实例
zhipu_vision_llm = create_zhipu_llm()
deepseek_text_llm = create_deepseek_llm()
