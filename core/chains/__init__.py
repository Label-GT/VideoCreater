"""
Chains 模块初始化
"""
from core.chains.video_analysis_chain import (
    VideoAnalysisChain,
    analyze_frames,
    create_video_analysis_chain
)
from core.chains.script_generation_chain import (
    ScriptGenerationChain,
    generate_scripts,
    create_script_generation_chain,
    create_theme_analysis_chain
)

__all__ = [
    # Video Analysis
    'VideoAnalysisChain',
    'analyze_frames',
    'create_video_analysis_chain',
    
    # Script Generation
    'ScriptGenerationChain',
    'generate_scripts',
    'create_script_generation_chain',
    'create_theme_analysis_chain',
]
