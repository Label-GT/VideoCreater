"""
文案生成 Chain 模块
使用 LangChain SequentialChain 实现多步骤文案生成
"""
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate

from core.models import deepseek_text_llm
from core.prompts import script_generation_prompt, STYLE_DESCRIPTIONS, theme_analysis_prompt


def calculate_max_chars(scene_duration: float, chars_per_second: float = 4.0) -> int:
    """计算场景允许的最大字符数"""
    return int(scene_duration * chars_per_second)


def create_script_generation_chain(style: str = "悬疑"):
    """
    创建文案生成 Chain
    
    Args:
        style: 解说风格
    
    Returns:
        可执行的 Chain 对象
    """
    style_description = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["悬疑"])
    
    # 构建 Chain
    chain = (
        RunnablePassthrough.assign(
            max_chars=lambda x: calculate_max_chars(x.get('scene_duration', 3.0)),
            style_description=lambda x: style_description
        )
        | script_generation_prompt.partial(style=style)
        | deepseek_text_llm
        | StrOutputParser()
    )
    
    return chain


def create_theme_analysis_chain():
    """
    创建主题分析 Chain
    用于分析整体视频的主题和叙事线索
    
    Returns:
        可执行的 Chain 对象
    """
    chain = (
        theme_analysis_prompt
        | deepseek_text_llm
        | StrOutputParser()
    )
    
    return chain


def generate_scripts(
    analyses: List[Dict[str, Any]],
    scenes: List[Dict[str, Any]],
    style: str,
    movie_name: str,
    scripts_dir: str,
    use_theme_context: bool = True,
    progress_callback=None
) -> List[Dict[str, Any]]:
    """
    为每个场景生成解说词
    
    Args:
        analyses: 画面分析结果列表
        scenes: 场景信息列表
        style: 解说风格
        movie_name: 电影名称
        scripts_dir: 输出目录
        use_theme_context: 是否使用主题上下文
        progress_callback: 进度回调函数
    
    Returns:
        文案列表
    """
    scripts = []
    chain = create_script_generation_chain(style)
    
    # 可选：先分析整体主题
    theme_context = None
    if use_theme_context and len(analyses) > 1:
        if progress_callback:
            progress_callback(0, len(analyses), "分析视频主题...")
        
        scene_descriptions = "\n".join([
            f"{i+1}. {a['description']}" for i, a in enumerate(analyses)
        ])
        
        try:
            theme_chain = create_theme_analysis_chain()
            theme_context = theme_chain.invoke({
                'scene_count': len(analyses),
                'scene_descriptions': scene_descriptions
            })
            print(f"视频主题分析：{theme_context[:200]}...")
        except Exception as e:
            print(f"主题分析失败：{e}，继续生成文案")
    
    # 为每个场景生成文案
    total_scenes = len(analyses)
    
    for i, analysis in enumerate(analyses):
        if progress_callback:
            progress_callback(i + 1, total_scenes, f"生成场景 {i+1}/{total_scenes} 解说词")
        
        # 查找对应场景信息
        scene = next(
            (item for item in scenes if item["index"] == analysis['scene_index']),
            None
        )
        
        if not scene:
            print(f"  警告：未找到场景 {analysis['scene_index']} 的信息")
            continue
        
        scene_duration = scene.get('duration', 3.0)
        
        # 构建输入
        input_data = {
            'scene_description': analysis['description'],
            'scene_duration': scene_duration,
            'style': style,
            'theme_context': theme_context or ""
        }
        
        try:
            # 执行 Chain
            script = chain.invoke(input_data)
            
            scripts.append({
                'scene_index': analysis['scene_index'],
                'timestamp': analysis['timestamp'],
                'time_str': analysis['time_str'],
                'description': analysis['description'],
                'script': script.strip(),
                'duration': scene_duration,
                'theme_context': theme_context
            })
            
            print(f"  场景{i+1}: {script.strip()[:50]}...")
            
        except Exception as e:
            print(f"  场景{i+1}生成失败：{e}")
            scripts.append({
                'scene_index': analysis['scene_index'],
                'timestamp': analysis['timestamp'],
                'time_str': analysis['time_str'],
                'description': analysis['description'],
                'script': "解说词生成失败",
                'duration': scene_duration,
                'theme_context': theme_context
            })
    
    # 保存文案
    os.makedirs(scripts_dir, exist_ok=True)
    
    # 保存 JSON 格式
    scripts_path = os.path.join(scripts_dir, f"{movie_name}_scripts.json")
    with open(scripts_path, 'w', encoding='utf-8') as f:
        json.dump(scripts, f, indent=2, ensure_ascii=False)
    
    # 保存纯文本格式
    text_path = os.path.join(scripts_dir, f"{movie_name}_script.txt")
    with open(text_path, 'w', encoding='utf-8') as f:
        for script in scripts:
            f.write(f"[{script['time_str']}] {script['script']}\n\n")
    
    print(f"文案已保存：{scripts_path}, {text_path}")
    
    return scripts


class ScriptGenerationChain:
    """
    文案生成 Chain 封装类
    提供更高级的接口，支持风格配置、批量生成等
    """
    
    def __init__(self, style: str = "悬疑", use_theme_context: bool = True):
        """
        初始化
        
        Args:
            style: 解说风格
            use_theme_context: 是否使用主题上下文
        """
        if style not in STYLE_DESCRIPTIONS:
            raise ValueError(f"不支持的风格：{style}，可选：{list(STYLE_DESCRIPTIONS.keys())}")
        
        self.style = style
        self.use_theme_context = use_theme_context
        self._chain = create_script_generation_chain(style)
        self._theme_chain = create_theme_analysis_chain() if use_theme_context else None
    
    def generate(
        self,
        analyses: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        movie_name: str,
        scripts_dir: str,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        生成解说文案
        
        Args:
            analyses: 画面分析结果
            scenes: 场景信息
            movie_name: 电影名称
            scripts_dir: 输出目录
            progress_callback: 进度回调
        
        Returns:
            文案列表
        """
        return generate_scripts(
            analyses=analyses,
            scenes=scenes,
            style=self.style,
            movie_name=movie_name,
            scripts_dir=scripts_dir,
            use_theme_context=self.use_theme_context,
            progress_callback=progress_callback
        )
    
    def generate_single(
        self,
        scene_description: str,
        scene_duration: float
    ) -> str:
        """
        为单个场景生成文案
        
        Args:
            scene_description: 场景描述
            scene_duration: 场景时长
        
        Returns:
            生成的文案
        """
        input_data = {
            'scene_description': scene_description,
            'scene_duration': scene_duration,
            'style': self.style
        }
        
        return self._chain.invoke(input_data)
