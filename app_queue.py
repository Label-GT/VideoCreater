# app_queue.py
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import gradio as gr
import os
import shutil
import time
from pathlib import Path
from celery.result import AsyncResult
from tasks import generate_narration, app

# 确保目录存在
os.makedirs("inputs", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# 设置 Gradio 临时目录
os.environ['GRADIO_TEMP_DIR'] = './inputs'

def submit_task(video_file, style):
    """提交视频处理任务"""
    if video_file is None:
        return None, "请先上传视频文件"
    
    try:
        video_path = video_file
        movie_name = Path(video_path).stem
        
        # 提交 Celery 任务
        task = generate_narration.delay(video_path, style, movie_name)
        
        return task.id, f"✅ 任务已提交！ID: {task.id}\n视频: {movie_name}\n风格: {style}"
    except Exception as e:
        return None, f"❌ 提交失败: {str(e)}"

def get_status(task_id):
    """查询任务状态"""
    if not task_id or task_id.strip() == "":
        return "⚠️ 请输入任务ID"
    
    try:
        result = AsyncResult(task_id, app=app)
        
        if result.ready():
            task_result = result.get(timeout=1)
            if task_result.get('status') == 'completed':
                output_path = task_result.get('output_path')
                return f"✅ 完成！\n视频路径: {output_path}"
            else:
                return f"❌ 失败: {task_result.get('error', '未知错误')}"
        else:
            if result.state == 'PROGRESS':
                info = result.info
                progress = info.get('progress', 0)
                stage = info.get('stage', '处理中')
                return f"⏳ 处理中... {progress}% - {stage}"
            else:
                return f"⏳ 状态: {result.state}"
                
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"

# 创建 Web 界面
with gr.Blocks(title="AI 电影解说视频生成器", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎬 AI 电影解说视频生成器（批量版）
    ### 上传电影文件，后台自动处理，支持批量提交
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
            submit_btn = gr.Button("🚀 提交任务", variant="primary", size="lg")
            task_id_display = gr.Textbox(label="任务ID", interactive=False)
            submit_status = gr.Textbox(label="提交状态", lines=3, interactive=False)
        
        with gr.Column(scale=1):
            task_id_input = gr.Textbox(label="任务ID", placeholder="输入任务ID查询")
            query_btn = gr.Button("🔍 查询状态", variant="secondary")
            status_output = gr.Textbox(label="任务状态", lines=8, interactive=False)
    
    # 绑定事件
    submit_btn.click(
        fn=submit_task,
        inputs=[video_input, style],
        outputs=[task_id_display, submit_status]
    )
    
    query_btn.click(
        fn=get_status,
        inputs=[task_id_input],
        outputs=[status_output]
    )
    
    gr.Markdown("""
    ---
    ### 📝 使用说明
    1. 上传 MP4 格式的电影文件
    2. 选择解说风格
    3. 点击「提交任务」
    4. 复制任务ID
    5. 随时查询任务进度
    6. 完成后会显示视频路径
    """)

if __name__ == "__main__":
    print("启动 Web 界面...")
    demo.launch(server_name="127.0.0.1", server_port=7860)