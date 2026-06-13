import os
os.environ['GRADIO_TEMP_DIR'] = './inputs'
import gradio as gr
import subprocess
import sys
import time
from pathlib import Path
import shutil
# 导入你的处理模块
from frame_extractor import get_video_info, extract_frames
from video_analyzer import analyze_frames_batch
from script_generator import generate_script, save_script
from tts_generator import process_tts
from video_composer import compose_video
from config import INPUT_DIR, OUTPUT_DIR

# 确保目录存在
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_video(video_file, style, progress=gr.Progress()):
    """
    处理视频的主函数，供 Gradio 调用
    """
    if video_file is None:
        return None, "请先上传视频文件"
    
    video_path = video_file
    movie_name = Path(video_path).stem
    
    progress(0, desc="开始处理...")
    
    try:
        # 1. 获取视频信息
        progress(0.05, desc="获取视频信息...")
        video_info = get_video_info(video_path)
        print(f"视频时长: {video_info['duration']:.2f}秒")
        print(f"分辨率: {video_info['width']}x{video_info['height']}")
        
        # 2. 提取关键帧
        progress(0.1, desc="提取关键帧...")
        frames = extract_frames(video_path, interval=30)
        print(f"共提取 {len(frames)} 个关键帧")
        
        # 3. 分析画面内容
        progress(0.2, desc="分析画面内容（可能需要2-3分钟）...")
        descriptions = analyze_frames_batch(frames, sample_rate=0.2)
        
        # 4. 生成解说文案
        progress(0.6, desc="生成解说文案...")
        script = generate_script(movie_name, descriptions, style)
        script_path = save_script(script, movie_name)
        
        # 5. 语音合成 + 字幕
        progress(0.7, desc="语音合成...")
        voice_path, subtitle_path = process_tts(script, movie_name)
        
        # 6. 合成最终视频
        progress(0.85, desc="合成视频...")
        output_path = compose_video(video_path, voice_path, subtitle_path, movie_name)
        
        progress(1.0, desc="完成！")
        
        return output_path, f"✅ 视频生成成功！"
        
    except Exception as e:
        import traceback
        error_msg = f"❌ 处理失败：{str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return None, error_msg

# 创建 Web 界面
def create_ui():
    with gr.Blocks(title="AI 电影解说视频生成器", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎬 AI 电影解说视频生成器
        ### 上传电影文件，AI 自动生成解说视频
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                video_input = gr.Video(
                    label="上传电影文件",
                    sources=["upload"],
                    format="mp4"
                )
                style = gr.Radio(
                    choices=["悬疑", "热血", "幽默", "温情"],
                    label="解说风格",
                    value="悬疑"
                )
                submit_btn = gr.Button("🚀 生成解说视频", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                video_output = gr.Video(label="生成的解说视频")
                status = gr.Textbox(label="处理状态", lines=5, interactive=False)
        
        # 绑定事件
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
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)