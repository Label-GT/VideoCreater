import os
from dotenv import load_dotenv

load_dotenv()

# API 配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "https://api.zhipu.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 路径配置
INPUT_DIR = "./inputs"
OUTPUT_DIR = "./outputs"
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
SCENES_DIR = os.path.join(OUTPUT_DIR, "scenes")
SCRIPTS_DIR = os.path.join(OUTPUT_DIR, "scripts")
VOICE_DIR = os.path.join(OUTPUT_DIR, "voice")
SUBTITLE_DIR = os.path.join(OUTPUT_DIR, "subtitles")
VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
TEMP_DIR = "./temp"

# 创建目录
for d in [INPUT_DIR, OUTPUT_DIR, FRAMES_DIR, SCENES_DIR, SCRIPTS_DIR, 
          VOICE_DIR, SUBTITLE_DIR, VIDEO_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)

# 场景检测参数
SCENE_THRESHOLD = 35.0      # 场景检测阈值
MAX_SCENES = 20              # 最大场景数
MIN_SCENE_DURATION = 1.0    # 最小场景时长（秒）

# 语音参数
TTS_VOICE = "zh-CN-YunxiNeural"

# 视频参数
VIDEO_FPS = 24
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
