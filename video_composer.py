from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
import os
from config import VIDEO_DIR
from moviepy.video.tools.subtitles import SubtitlesClip
import re
from moviepy.tools import cvsecs

def add_subtitle_to_video(video_clip, subtitle_path, fontsize=30, color='white',
                          stroke_color='black', stroke_width=1):
    """添加字幕到视频（手动解析，绕过编码问题）"""
    # 1. 用 UTF-8 读取文件
    with open(subtitle_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 2. 手动解析 SRT
    times_texts = []
    current_times = None
    current_text = ""
    
    for line in content.splitlines():
        times = re.findall("([0-9]*:[0-9]*:[0-9]*,[0-9]*)", line)
        if times:
            current_times = [cvsecs(t) for t in times]
        elif line.strip() == '' and current_times is not None:
            times_texts.append((current_times, current_text.strip('\n')))
            current_times, current_text = None, ""
        elif current_times is not None:
            current_text += line + '\n'
    
    # 3. 传入解析结果
    generator = lambda txt: TextClip(
        txt, font='SimHei', fontsize=fontsize, color=color,
        stroke_color=stroke_color, stroke_width=stroke_width,
        method='caption'
    )
    subtitles = SubtitlesClip(times_texts, generator)  # 传列表，不传路径
    
    return CompositeVideoClip([video_clip, subtitles.set_position(('center', 'bottom'))])

def compose_video(video_path: str, voice_path: str, subtitle_path: str, 
                  movie_name: str, bgm_path: str = None) -> str:
    """
    合成最终视频
    video_path: 原始视频路径
    voice_path: 配音路径
    subtitle_path: 字幕路径
    movie_name: 电影名称（用于输出文件名）
    bgm_path: 背景音乐路径（可选）
    """
    os.makedirs(VIDEO_DIR, exist_ok=True)
    output_path = os.path.join(VIDEO_DIR, f"{movie_name}_final.mp4")
    
    print("加载视频...")
    video = VideoFileClip(video_path)
    
    print("添加配音...")
    audio = AudioFileClip(voice_path)
    
    # 如果配音比视频短，循环视频或裁剪；这里简单裁剪到配音长度
    if audio.duration < video.duration:
        video = video.subclip(0, audio.duration)
    
    video = video.set_audio(audio)
    
    print("添加字幕...")
    #video_with_subs = add_subtitle_to_video(video, subtitle_path)
    print("跳过字幕添加...")
    video_with_subs = video
    
    # 可选：添加背景音乐（降低音量作为背景）
    if bgm_path and os.path.exists(bgm_path):
        bgm = AudioFileClip(bgm_path).volumex(0.3)
        # 循环BGM到视频长度
        bgm = bgm.loop(duration=audio.duration)
        final_audio = CompositeAudioClip([audio, bgm])
        video_with_subs = video_with_subs.set_audio(final_audio)
    
    print("导出视频...")
    video_with_subs.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    
    # 关闭资源
    video.close()
    audio.close()
    if bgm_path:
        bgm.close()
    video_with_subs.close()
    
    return output_path
