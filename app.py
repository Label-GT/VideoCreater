#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gradio Web 界面入口
使用重构后的 Pipeline
"""
import os
import sys
import traceback
from pathlib import Path

# 设置 Gradio 临时目录
os.environ['GRADIO_TEMP_DIR'] = './inputs'

import gradio as gr

from config import INPUT_DIR, MAX_SCENES, MIN_SCENE_DURATION, OUTPUT_DIR, SCENE_THRESHOLD, TTS_VOICE
from core.pipeline import NarrationPipeline


def process_video(video_file, style, bgm_file=None, bgm_volume=0.3, progress=gr.Progress()):
    """
    处理视频生成解说
    
    Args:
        video_file: 上传的视频文件
        style: 解说风格
        bgm_file: 背景音乐文件（可选）
        bgm_volume: BGM 音量（0-1，默认 0.3）
        progress: Gradio 进度对象
    
    Returns:
        (输出视频路径，状态消息)
    """
    if video_file is None:
        return None, "请先上传视频文件"
    
    video_path = video_file
    movie_name = Path(video_path).stem
    
    try:
        # 创建 Pipeline 实例（使用 config 中的配置）
        pipeline = NarrationPipeline(
            style=style,
            scene_threshold=SCENE_THRESHOLD,
            max_scenes=MAX_SCENES,
            min_scene_duration=MIN_SCENE_DURATION,
            tts_voice=TTS_VOICE,
            output_base_dir=OUTPUT_DIR
        )
        
        # 定义进度回调
        def progress_callback(current, total, message):
            percent = current / total
            progress(percent, desc=message)
            print(f"[{current}/{total}] {message}")
        
        # 准备 BGM 参数
        bgm_path = bgm_file.name if bgm_file else None
        
        # 执行 Pipeline
        result = pipeline.execute(
            video_path=video_path,
            movie_name=movie_name,
            progress_callback=progress_callback,
            bgm_path=bgm_path,
            bgm_volume=bgm_volume
        )
        
        # 处理结果
        if result['status'] == 'success':
            total_duration = result['total_duration']
            status_msg = (
                f"✅ 视频生成成功！\n"
                f"场景数：{result['scene_count']}\n"
                f"总时长：{total_duration:.1f}秒\n"
                f"输出：{result['output_path']}"
            )
            return result['output_path'], status_msg
        else:
            error_msg = f"❌ 处理失败：{result['error']}"
            if 'traceback' in result:
                error_msg += f"\n\n{result['traceback']}"
            print(error_msg)
            return None, error_msg
            
    except Exception as e:
        error_msg = f"❌ 处理失败：{str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return None, error_msg


# 创建 Web 界面
def create_ui():
    """创建 Gradio 界面"""
    with gr.Blocks(title="AI 电影解说视频生成器") as demo:
        gr.Markdown("""
        # 🎬 AI 电影解说视频生成器
        ### 智能场景检测 + 音画同步
        
        基于 LangChain 重构的 AI 视频处理系统
        """)
        
        with gr.Row():
            with gr.Column():
                video_input = gr.Video(
                    label="上传电影",
                    sources=["upload"],
                    format="mp4"
                )
                style = gr.Radio(
                    choices=["悬疑", "热血", "幽默", "温情"],
                    label="解说风格",
                    value="悬疑"
                )
                
                with gr.Accordion("🎵 背景音乐设置", open=False):
                    bgm_file = gr.File(
                        label="上传背景音乐（可选）",
                        file_types=[".mp3", ".wav", ".ogg", ".m4a"],
                        value=None
                    )
                    
                    bgm_volume = gr.Slider(
                        minimum=0,
                        maximum=1,
                        value=0.3,
                        step=0.05,
                        label="背景音乐音量（0-100%，默认 30%）"
                    )
                    
                    bgm_generate_btn = gr.Button(
                        "🎵 AI 生成背景音乐（即将推出）",
                        variant="secondary",
                        interactive=False
                    )
                
                submit_btn = gr.Button("🚀 生成解说视频", variant="primary")
            
            with gr.Column():
                video_output = gr.Video(label="生成的解说视频")
                status = gr.Textbox(
                    label="状态",
                    lines=10,
                    interactive=False
                )
        
        submit_btn.click(
            fn=process_video,
            inputs=[video_input, style, bgm_file, bgm_volume],
            outputs=[video_output, status]
        )
        
        # 示例说明
        gr.Markdown("""
        ---
        ### 📝 使用说明
        1. 上传 MP4 格式的电影文件
        2. 选择解说风格（悬疑/热血/幽默/温情）
        3. 点击"生成解说视频"，等待 3-5 分钟
        4. 下载生成的解说视频
        
        ### 🔧 技术特性
        - **智能场景检测**: 自动识别场景切换
        - **AI 视觉分析**: 智谱 AI 分析画面内容
        - **智能文案生成**: DeepSeek 生成风格化解说词
        - **语音合成**: Edge-TTS 自然语音
        - **视频合成**: 自动对齐音画
        """)
    
    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        theme=gr.themes.Soft()
    )
