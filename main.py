#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命令行交互入口
使用重构后的 Pipeline
"""
import sys
from pathlib import Path

from config import INPUT_DIR, MAX_SCENES, MIN_SCENE_DURATION, SCENE_THRESHOLD, TTS_VOICE
from core.pipeline import generate_narration_video

def main():
    """命令行交互入口"""
    print("=" * 60)
    print("🎬 AI 电影解说视频生成器")
    print("=" * 60)
    
    # 1. 输入电影文件路径
    print("\n请输入电影文件路径：")
    video_path = input("> ").strip()
    
    if not video_path:
        # 使用默认测试文件
        test_file = Path(INPUT_DIR) / "test.mp4"
        if test_file.exists():
            video_path = str(test_file)
            print(f"使用默认文件：{video_path}")
        else:
            print("❌ 未提供有效的视频文件路径")
            return
    
    if not Path(video_path).exists():
        print(f"❌ 文件不存在：{video_path}")
        return
    
    # 2. 输入电影名称
    print("\n请输入电影名称（直接回车使用文件名）：")
    movie_name = input("> ").strip()
    if not movie_name:
        movie_name = Path(video_path).stem
    
    # 3. 选择解说风格
    print("\n选择解说风格：")
    print("  1. 悬疑")
    print("  2. 热血")
    print("  3. 幽默")
    print("  4. 温情")
    
    style_map = {
        '1': '悬疑',
        '2': '热血',
        '3': '幽默',
        '4': '温情'
    }
    
    while True:
        choice = input("> ").strip()
        if choice in style_map:
            style = style_map[choice]
            break
        print("请输入 1-4 之间的数字")
    
    # 4. 执行处理流程
    print(f"\n🚀 开始处理：{movie_name}")
    print(f"风格：{style}")
    print("-" * 60)
    
    def progress_callback(current, total, message):
        """进度回调"""
        percent = int(current / total * 100)
        print(f"[{percent:3d}%] {message}")
    
    result = generate_narration_video(
        video_path=video_path,
        style=style,
        movie_name=movie_name,
        scene_threshold=SCENE_THRESHOLD,
        max_scenes=MAX_SCENES,
        min_scene_duration=MIN_SCENE_DURATION,
        tts_voice=TTS_VOICE,
        progress_callback=progress_callback
    )
    
    # 5. 输出结果
    print("\n" + "=" * 60)
    if result['status'] == 'success':
        print(f"✅ 视频生成成功！")
        print(f"场景数：{result['scene_count']}")
        print(f"总时长：{result['total_duration']:.1f}秒")
        print(f"输出路径：{result['output_path']}")
    else:
        print(f"❌ 处理失败：{result['error']}")
        if 'traceback' in result:
            print("\n详细错误：")
            print(result['traceback'])
    
    print("=" * 60)


if __name__ == "__main__":
    main()
