# app_queue.py
import gradio as gr
from celery.result import AsyncResult
from tasks import test_task

# 存储任务
tasks_store = {}

def submit_task(message):
    task = test_task.delay(message)
    tasks_store[task.id] = {'status': 'pending'}
    return task.id, f"任务已提交: {task.id}"

def get_status(task_id):
    result = AsyncResult(task_id)
    # 查看对象类型
    print(type(result))  # <class 'celery.result.AsyncResult'>

    # 查看所有可用方法和属性
    print(dir(result))
    
    if result.ready():
        return result.result
    else:
        return f"处理中... {result.info}"

with gr.Blocks() as demo:
    gr.Markdown("# Celery 测试")
    
    with gr.Row():
        msg_input = gr.Textbox(label="消息")
        submit_btn = gr.Button("提交")
        task_id_output = gr.Textbox(label="任务ID")
    
    with gr.Row():
        task_id_input = gr.Textbox(label="查询任务ID")
        query_btn = gr.Button("查询状态")
        status_output = gr.Textbox(label="状态", lines=3)
    
    submit_btn.click(submit_task, [msg_input], [task_id_output])
    query_btn.click(get_status, [task_id_input], [status_output])

if __name__ == "__main__":
    demo.launch()