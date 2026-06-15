import os
import subprocess
import json
from moviepy import *
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.AudioClip import CompositeAudioClip
from config import VIDEO_DIR, SUBTITLE_DIR, VIDEO_FPS, VIDEO_CODEC, AUDIO_CODEC

def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt(scripts: list, voice_durations: list, movie_name: str) -> str:
    """生成 SRT 字幕文件"""
    srt_content = ""
    current_time = 0.0
    
    for i, (script, duration) in enumerate(zip(scripts, voice_durations)):
        start_time = current_time
        end_time = current_time + duration
        
        srt_content += f"{i+1}\n"
        srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
        srt_content += f"{script['script']}\n\n"
        
        current_time = end_time
    
    subtitle_path = os.path.join(SUBTITLE_DIR, f"{movie_name}.srt")
    with open(subtitle_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    print(f"  字幕已保存: {subtitle_path}")
    return subtitle_path

def add_subtitle_ffmpeg(video_path: str, subtitle_path: str, output_path: str) -> str:
    """使用 FFmpeg 添加硬字幕"""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"subtitles={subtitle_path}:force_style='FontName=SimHei,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1'",
        "-c:a", "copy",
        output_path, "-y"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg 字幕添加失败: {result.stderr[:200]}")
        return video_path
    
    return output_path

def compose_sync_video(video_path: str, scenes: list, scripts: list, voice_paths: list, voice_durations: list, movie_name: str) -> str:
    """合成最终视频（定格适配）"""
    print("  加载原视频...")
    video = VideoFileClip(video_path)
    video_clips = []
    audio_clips = []
    
    for i, (scene, script, voice_path, voice_duration) in enumerate(zip(scenes, scripts, voice_paths, voice_durations)):
        scene_start = scene['start']
        scene_end = scene['end']
        scene_duration = scene_end - scene_start
        
        print(f"  处理场景 {i+1}: 原{scene_duration:.1f}s → 配音{voice_duration:.1f}s")
        
        if voice_duration <= scene_duration:
            # 配音短：裁剪场景
            scene_clip = video.subclipped(scene_start, scene_start + voice_duration)
        else:
            # 配音长：正常播放 + 定格最后一帧
            scene_clip = video.subclipped(scene_start, scene_end)
            last_frame = scene_clip.get_frame(scene_clip.duration - 0.04)
            freeze_duration = voice_duration - scene_duration
            freeze_clip = ImageClip(last_frame, duration=freeze_duration)
            scene_clip = concatenate_videoclips([scene_clip, freeze_clip])
            print(f"    定格 {freeze_duration:.1f}秒")
        
        video_clips.append(scene_clip)
        audio_clips.append(AudioFileClip(voice_path))
    
    print("  拼接视频片段...")
    final_video = concatenate_videoclips(video_clips)
    
    print("  拼接音频...")
    final_audio = CompositeAudioClip(audio_clips)
    final_video = final_video.with_audio(final_audio)
    
    # 输出无字幕版本
    temp_output = os.path.join(VIDEO_DIR, f"{movie_name}_temp.mp4")
    final_video.write_videofile(temp_output, fps=VIDEO_FPS, codec=VIDEO_CODEC, audio_codec=AUDIO_CODEC)
    
    # 清理资源
    video.close()
    final_video.close()
    for clip in video_clips:
        clip.close()
    for audio in audio_clips:
        audio.close()
    
    # 生成字幕
    subtitle_path = generate_srt(scripts, voice_durations, movie_name)
    
    # 添加字幕
    output_path = os.path.join(VIDEO_DIR, f"{movie_name}_final.mp4")
    final_path = add_subtitle_ffmpeg(temp_output, subtitle_path, output_path)
    
    # 删除临时文件
    if os.path.exists(temp_output) and temp_output != final_path:
        os.remove(temp_output)
    
    print(f"  视频已保存: {final_path}")
    return final_path