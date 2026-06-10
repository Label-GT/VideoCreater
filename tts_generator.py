import asyncio
import edge_tts
import os
import re
from config import TTS_VOICE, VOICE_DIR, SUBTITLE_DIR

async def text_to_speech_async(text: str, output_path: str, voice: str = TTS_VOICE):
    """异步合成语音，逐块写入文件"""
    communicate = edge_tts.Communicate(text, voice)
    
    # 使用流式写入，确保数据真正写入
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
    
    # 验证文件大小
    if os.path.getsize(output_path) == 0:
        raise Exception("生成的音频文件为空，请检查网络连接")

def text_to_speech(text: str, output_path: str, voice: str = TTS_VOICE):
    """同步包装，方便调用"""
    asyncio.run(text_to_speech_async(text, output_path, voice))
    return output_path

def generate_subtitle_from_script(script: str, output_path: str, duration_per_char: float = 0.25):
    """
    根据文案手动生成字幕（不依赖 edge-tts）
    """
    if not script or len(script.strip()) == 0:
        raise Exception(f"文案为空，无法生成字幕")
    
    # 按标点分句
    sentences = re.split(r'([。！？!?])', script)
    full_sentences = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            full_sentences.append((sentences[i] + sentences[i+1]).strip())
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        full_sentences.append(sentences[-1].strip())
    
    # 过滤空句子
    full_sentences = [s for s in full_sentences if s]
    
    if not full_sentences:
        raise Exception("未能从文案中提取到有效句子")
    
    print(f"  提取到 {len(full_sentences)} 个句子")
    
    # 生成 SRT
    srt_content = ""
    current_time = 0.0
    
    for i, sentence in enumerate(full_sentences):
        # 每句时长：基础1.5秒 + 字数*0.2秒，最长8秒
        duration = min(8.0, max(1.5, len(sentence) * 0.2))
        
        start_time = current_time
        end_time = current_time + duration
        
        def fmt(t):
            hours = int(t // 3600)
            minutes = int((t % 3600) // 60)
            seconds = int(t % 60)
            millis = int((t % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
        
        srt_content += f"{i+1}\n{fmt(start_time)} --> {fmt(end_time)}\n{sentence}\n\n"
        current_time += duration
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    print(f"  字幕生成成功：{len(full_sentences)} 条，总时长 {current_time:.1f} 秒")
    return output_path

def process_tts(script: str, movie_name: str) -> tuple:
    """
    完整处理语音合成和字幕生成
    返回 (voice_path, subtitle_path)
    """
    # 添加调试信息
    print(f"文案长度: {len(script)} 字符")
    print(f"文案前200字符: {script[:200]}")
    
    if not script or len(script.strip()) == 0:
        raise Exception("文案为空，无法合成语音")

    os.makedirs(VOICE_DIR, exist_ok=True)
    os.makedirs(SUBTITLE_DIR, exist_ok=True)
    
    voice_path = os.path.join(VOICE_DIR, f"{movie_name}_voice.mp3")
    subtitle_path = os.path.join(SUBTITLE_DIR, f"{movie_name}_subtitle.srt")
    
    print("正在合成语音...")
    text_to_speech(script, voice_path)
    
    # 验证文件大小
    if os.path.getsize(voice_path) == 0:
        raise Exception(f"语音文件生成失败：{voice_path} 大小为 0")
    print(f"语音生成成功，大小：{os.path.getsize(voice_path)} 字节")
    
    print("正在生成字幕...")
    generate_subtitle_from_script(script, subtitle_path)  # ← 不用异步
    
    return voice_path, subtitle_path
