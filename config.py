import os
from dotenv import load_dotenv

load_dotenv()

# API配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "https://api.zhipu.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 路径配置
INPUT_DIR = "./inputs"
OUTPUT_DIR = "./outputs"
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
SCRIPTS_DIR = os.path.join(OUTPUT_DIR, "scripts")
VOICE_DIR = os.path.join(OUTPUT_DIR, "voice")
SUBTITLE_DIR = os.path.join(OUTPUT_DIR, "subtitles")
VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")

# 参数配置
FRAME_INTERVAL = 30  # 每隔30秒抽一帧
TTS_VOICE = "zh-CN-YunxiNeural"  # 配音音色
