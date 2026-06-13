#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frame_extractor import extract_frames, get_video_info
from video_analyzer import analyze_frames_batch
from script_generator import generate_script, save_script
from tts_generator import process_tts
from video_composer import compose_video
from config import INPUT_DIR

def ensure_dirs():
    """确保所有必要的目录存在"""
    dirs = [
        "./inputs", "./outputs",
        "./outputs/frames", "./outputs/audio", 
        "./outputs/scripts", "./outputs/voice",
        "./outputs/subtitles", "./outputs/videos"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def main():
    start_time = time.time()
    print("=" * 50)
    print("电影解说视频生成器 v1.0")
    print("=" * 50)
    
    # 确保目录存在
    ensure_dirs()
    
    # 1. 获取用户输入
    video_path = input("请输入电影文件路径: ").strip().strip('"').strip("'")
    if not os.path.exists(video_path):
        print(f"错误：文件不存在 - {video_path}")
        return
    
    movie_name = input("请输入电影名称: ").strip()
    if not movie_name:
        movie_name = Path(video_path).stem
    
    style = input("请选择解说风格（悬疑/喜剧/热血/温情，默认悬疑）: ").strip()
    if not style:
        style = "悬疑"
    
    print("\n" + "=" * 50)
    print("开始处理...")
    print("=" * 50)
    
    # 2. 获取视频信息
    print("\n[1/7] 获取视频信息...")
    step_start = time.time()
    video_info = get_video_info(video_path)
    print(f"[1/7] 获取视频信息... 耗时: {time.time() - step_start:.1f}秒")
    print(f"视频时长: {video_info['duration']:.2f}秒")
    print(f"分辨率: {video_info['width']}x{video_info['height']}")
    
    # 3. 提取关键帧
    print("\n[2/7] 提取关键帧...")
    step_start = time.time()
    frames = extract_frames(video_path, interval=30)
    print(f"[2/7] 提取关键帧... 耗时: {time.time() - step_start:.1f}秒, 共{len(frames)}帧")
    print(f"共提取 {len(frames)} 个关键帧")
    
    # 4. 分析画面
    print("\n[3/7] 分析画面内容（此步骤耗时较长）...")
    step_start = time.time()
    descriptions = analyze_frames_batch(frames, sample_rate=0.2)
    print(f"[3/7] 分析画面内容... 耗时: {time.time() - step_start:.1f}秒")
    
    # 5. 生成解说文案
    print("\n[4/7] 生成解说文案...")
    step_start = time.time()
    script = generate_script(movie_name, descriptions, style)
    # 添加验证
    if not script or len(script.strip()) == 0:
        print("错误：生成的文案为空！")
        return

    script_path = save_script(script, movie_name)
    print(f"[4/7] 生成解说文案... 耗时: {time.time() - step_start:.1f}秒")
    print(f"文案已保存: {script_path}")
    print(f"\n文案预览：\n{script[:300]}...\n")
    
    # 6. 语音合成+字幕
    print("\n[5/7] 语音合成及字幕生成...")
    step_start = time.time()
    voice_path, subtitle_path = process_tts(script, movie_name)
    print(f"[5/7] 语音合成及字幕生成... 耗时: {time.time() - step_start:.1f}秒")
    print(f"配音已保存: {voice_path}")
    print(f"字幕已保存: {subtitle_path}")
    
    # 7. 合成最终视频
    print("\n[6/7] 合成最终视频...")
    # 可选：添加背景音乐，暂时不添加
    step_start = time.time()
    output_path = compose_video(video_path, voice_path, subtitle_path, movie_name)
    print(f"[6/7] 合成最终视频... 耗时: {time.time() - step_start:.1f}秒")
    print(f"视频已保存: {output_path}")
    
    print("\n[7/7] 完成！")
    print(f"\n✅ 解说视频已生成：{output_path}")

    total_time = time.time() - start_time
    print(f"\n📊 统计：总耗时 {total_time:.1f}秒，共 {len(frames)} 帧")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
