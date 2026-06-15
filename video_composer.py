from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips, ImageClip
from moviepy.audio.AudioClip import concatenate_audioclips

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

def compose_video_by_scenes(video_path: str, segments: list, voice_paths: list, movie_name: str) -> str:
    """按场景裁剪并拼接视频"""
    
    video = VideoFileClip(video_path)
    video_clips = []
    
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        
        # 确保时间在有效范围内
        start = max(0, min(start, video.duration - 0.5))
        end = min(end, video.duration)
        
        if end > start:
            clip = video.subclip(start, end)
            video_clips.append(clip)
            print(f"  裁剪场景 {i+1}: {start:.1f}s -> {end:.1f}s")
    
    if not video_clips:
        # 回退到完整视频
        video_clips = [video.subclip(0, min(video.duration, 60))]
    
    # 合并视频片段
    final_video = concatenate_videoclips(video_clips) if len(video_clips) > 1 else video_clips[0]
    
    # 合并配音
    audio_clips = [AudioFileClip(p) for p in voice_paths if os.path.exists(p)]
    if audio_clips:
        final_audio = concatenate_audioclips(audio_clips)
        final_video = final_video.set_audio(final_audio)
    
    output_path = os.path.join(VIDEO_DIR, f"{movie_name}_sync.mp4")
    final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    
    video.close()
    final_video.close()
    
    return output_path

def compose_sync_video(video_path: str, scenes: list, voice_paths: list, movie_name: str) -> str:
    """
    按场景裁剪，定格最后一帧，保证配音完整播放
    """
    video = VideoFileClip(video_path)
    video_clips = []
    audio_clips = []
    
    for i, scene in enumerate(scenes):
        voice_path = voice_paths[i]
        voice_duration = get_audio_duration(voice_path)
        scene_start = scene['start']
        scene_end = scene['end']
        scene_duration = scene_end - scene_start
        
        if voice_duration <= scene_duration:
            # 配音短：直接裁剪场景，不需要定格
            scene_clip = video.subclip(scene_start, scene_start + voice_duration)
        else:
            # 配音长：正常播放场景 + 最后一帧定格
            # 先取完整场景
            scene_clip = video.subclip(scene_start, scene_end)
            # 获取最后一帧
            last_frame = scene_clip.get_frame(scene_clip.duration - 0.04)
            # 创建定格画面（填补剩余时间）
            freeze_duration = voice_duration - scene_duration
            freeze_clip = ImageClip(last_frame, duration=freeze_duration)
            # 拼接：正常场景 + 定格画面
            scene_clip = concatenate_videoclips([scene_clip, freeze_clip])
        
        video_clips.append(scene_clip)
        audio_clips.append(AudioFileClip(voice_path))
        
        print(f"  场景{i+1}: 原{scene_duration:.1f}s → 配音{voice_duration:.1f}s" + 
              (f" (定格{voice_duration-scene_duration:.1f}s)" if voice_duration > scene_duration else ""))
    
    # 拼接所有场景
    final_video = concatenate_videoclips(video_clips)
    final_audio = concatenate_audioclips(audio_clips)
    final_video = final_video.set_audio(final_audio)
    
    output_path = os.path.join(VIDEO_DIR, f"{movie_name}_final.mp4")
    final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    
    # 清理资源
    video.close()
    final_video.close()
    for clip in video_clips:
        clip.close()
    for audio in audio_clips:
        audio.close()
    
    return output_path

def get_audio_duration(audio_path: str) -> float:
    """获取音频时长（秒）"""
    from pydub import AudioSegment
    audio = AudioSegment.from_mp3(audio_path)
    return len(audio) / 1000.0