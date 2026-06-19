"""
Prompt 模板定义模块
使用 LangChain PromptTemplate 管理所有提示词
"""
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

# ========== 视频分析 Prompt ==========

VIDEO_ANALYSIS_SYSTEM_PROMPT = """你是一个专业的视频内容分析师。
你的任务是观看视频画面，用简洁生动的语言描述正在发生的事情。

要求：
1. 描述要具体，包含人物、动作、场景、情绪等关键信息
2. 语言要生动，有画面感
3. 每段描述控制在 100 字以内
4. 重点关注戏剧性、冲突性、情感性的内容
"""

VIDEO_ANALYSIS_HUMAN_PROMPT = """这是视频 {timestamp} 时刻的画面。
请描述这个场景：正在发生什么？有什么关键细节？

画面内容：{image_url}
"""

video_analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", VIDEO_ANALYSIS_SYSTEM_PROMPT),
    ("human", VIDEO_ANALYSIS_HUMAN_PROMPT),
])


# ========== 文案生成 Prompt ==========

SCRIPT_GENERATION_SYSTEM_PROMPT = """你是一位专业的电影解说博主，擅长用{style}风格讲述故事。

你的任务是根据画面描述，生成一句精彩的解说词。

要求：
1. 严格控制在{max_chars}字以内
2. 语言风格：{style_description}
3. 要有悬念感/节奏感，吸引观众继续观看
4. 直接输出解说词，不要任何其他内容
"""

STYLE_DESCRIPTIONS = {
    "悬疑": "神秘、紧张，多用疑问句，制造悬念和期待感",
    "热血": "激昂、振奋，多用感叹句，强调冲突和胜利",
    "幽默": "轻松、诙谐，适当加入调侃和吐槽，让人会心一笑",
    "温情": "温暖、感性，注重情感表达，触动人心"
}

SCRIPT_GENERATION_HUMAN_PROMPT = """场景内容：{scene_description}
场景时长：{scene_duration}秒

请生成一句{style}风格的解说词（{max_chars}字以内）：
"""

script_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", SCRIPT_GENERATION_SYSTEM_PROMPT),
    ("human", SCRIPT_GENERATION_HUMAN_PROMPT),
])


# ========== 全局主题分析 Prompt ==========

THEME_ANALYSIS_SYSTEM_PROMPT = """你是一个专业的电影策划人。
你的任务是分析多个场景的描述，总结视频的整体主题、基调和叙事线索。

请输出：
1. 视频主题（一句话概括）
2. 情感基调（如：紧张、欢乐、感动等）
3. 主要人物/元素
4. 叙事建议（如何串联这些场景）
"""

THEME_ANALYSIS_HUMAN_PROMPT = """以下是视频的{scene_count}个场景描述：

{scene_descriptions}

请分析这个视频的整体主题和叙事线索。
"""

theme_analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", THEME_ANALYSIS_SYSTEM_PROMPT),
    ("human", THEME_ANALYSIS_HUMAN_PROMPT),
])


# ========== 文案润色 Prompt ==========

SCRIPT_REFINEMENT_SYSTEM_PROMPT = """你是专业的文案编辑。
你的任务是优化解说词，使其更流畅、更有感染力。

要求：
1. 保持原意不变
2. 优化语序和用词
3. 增强节奏感和韵律感
4. 确保符合{style}风格
"""

SCRIPT_REFINEMENT_HUMAN_PROMPT = """原始解说词：{original_script}
前后文：{context}

请优化这段解说词：
"""

script_refinement_prompt = ChatPromptTemplate.from_messages([
    ("system", SCRIPT_REFINEMENT_SYSTEM_PROMPT),
    ("human", SCRIPT_REFINEMENT_HUMAN_PROMPT),
])


# 模块导出
__all__ = [
    'VIDEO_ANALYSIS_SYSTEM_PROMPT',
    'VIDEO_ANALYSIS_HUMAN_PROMPT',
    'video_analysis_prompt',
    'SCRIPT_GENERATION_SYSTEM_PROMPT',
    'SCRIPT_GENERATION_HUMAN_PROMPT',
    'STYLE_DESCRIPTIONS',
    'script_generation_prompt',
    'theme_analysis_prompt',
    'script_refinement_prompt',
]
