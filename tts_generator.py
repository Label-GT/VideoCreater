import asyncio
import edge_tts
import os
import json
from config import TTS_VOICE, VOICE_DIR, SUBTITLE_DIR
from pydub import AudioSegment

async def text_to_speech_async(text: str, output_path: str, voice: str = TTS_VOICE):
    communicate = edge_tts.Communicate(text, voice)
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])

def text_to_speech(text: str, output_path: str):
    asyncio.run(text_to_speech_async(text, output_path))

def get_audio_duration(audio_path: str) -> float:
    """获取音频时长（秒）"""
    audio = AudioSegment.from_mp3(audio_path)
    return len(audio) / 1000.0

def process_tts(scripts: list, movie_name: str) -> tuple:
    """为每个场景生成配音"""
    voice_paths = []
    voice_durations = []
    
    for script in scripts:
        voice_path = os.path.join(VOICE_DIR, f"{movie_name}_scene_{script['scene_index']:04d}.mp3")
        print(f"  合成语音: {voice_path}")
        
        text_to_speech(script['script'], voice_path)
        
        duration = get_audio_duration(voice_path)
        voice_paths.append(voice_path)
        voice_durations.append(duration)
        
        script['voice_duration'] = duration
        script['voice_path'] = voice_path
        
        print(f"    时长: {duration:.1f}秒")
    
    # 保存更新后的 scripts（包含配音信息）
    scripts_path = os.path.join(VOICE_DIR, f"{movie_name}_voice_info.json")
    with open(scripts_path, 'w', encoding='utf-8') as f:
        json.dump(scripts, f, indent=2, ensure_ascii=False)
    
    return voice_paths, voice_durations