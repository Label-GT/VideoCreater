#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import asyncio

# 修复 Windows asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 设置 Gradio 临时目录
os.environ['GRADIO_TEMP_DIR'] = './inputs'

import gradio as gr
from pathlib import Path
from config import INPUT_DIR, OUTPUT_DIR, VIDEO_DIR
from frame_extractor import get_video_info, detect_scenes, extract_keyframes
from video_analyzer import analyze_scenes
from script_generator import generate_scripts
from tts_generator import process_tts
from video_composer import compose_sync_video

def process_video(video_file, style, progress=gr.Progress()):
    if video_file is None:
        return None, "请先上传视频文件"
    
    video_path = video_file
    movie_name = Path(video_path).stem
    
    try:
        # 1. 获取视频信息
        progress(0.02, desc="获取视频信息...")
        video_info = get_video_info(video_path)
        print(f"视频时长: {video_info['duration']:.1f}秒, 分辨率: {video_info['width']}x{video_info['height']}")
        
        # 2. 场景检测
        progress(0.05, desc="检测场景...")
        scenes = detect_scenes(video_path, movie_name)
        
        # 3. 提取关键帧
        progress(0.10, desc="提取关键帧...")
        frames = extract_keyframes(video_path, scenes, movie_name)
        
        # 4. 分析画面
        progress(0.20, desc="分析画面内容...")
        analyses = analyze_scenes(frames, movie_name)
        
        # 5. 生成解说词
        progress(0.50, desc="生成解说词...")
        scripts = generate_scripts(analyses, scenes, style, movie_name)
        
        # 6. 语音合成
        progress(0.70, desc="语音合成...")
        voice_paths, voice_durations = process_tts(scripts, movie_name)
        
        # 7. 合成视频
        progress(0.85, desc="合成视频...")
        output_path = compose_sync_video(video_path, scenes, scripts, voice_paths, voice_durations, movie_name)
        
        progress(1.0, desc="完成！")
        
        total_duration = sum(voice_durations)
        return output_path, f"✅ 视频生成成功！\n场景数: {len(scenes)}\n总时长: {total_duration:.1f}秒"
        
    except Exception as e:
        import traceback
        error_msg = f"❌ 处理失败: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return None, error_msg

# 创建 Web 界面
def create_ui():
    with gr.Blocks(title="AI 电影解说视频生成器", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎬 AI 电影解说视频生成器
        ### 智能场景检测 + 音画同步
        """)
        
        with gr.Row():
            with gr.Column():
                video_input = gr.Video(label="上传电影", sources=["upload"], format="mp4")
                style = gr.Radio(choices=["悬疑", "热血", "幽默", "温情"], label="解说风格", value="悬疑")
                submit_btn = gr.Button("🚀 生成解说视频", variant="primary")
            
            with gr.Column():
                video_output = gr.Video(label="生成的解说视频")
                status = gr.Textbox(label="状态", lines=10, interactive=False)
        
        submit_btn.click(
            fn=process_video,
            inputs=[video_input, style],
            outputs=[video_output, status]
        )
        
        # 示例说明
        gr.Markdown("""
        ---
        ### 📝 使用说明
        1. 上传 MP4 格式的电影文件
        2. 选择解说风格
        3. 点击生成，等待 3-5 分钟
        4. 下载生成的解说视频
        """)
    
    return demo

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860)