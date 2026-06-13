import base64
import time
from openai import OpenAI, RateLimitError
from config import ZHIPU_API_KEY, ZHIPU_BASE_URL

client = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL)

def encode_image(image_path: str) -> str:
    """将图片编码为base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def analyze_single_frame(frame_path: str, max_retries=5) -> str:
    """分析单张关键帧，带自动重试"""    
    with open(frame_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode()
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="glm-4.6v-flash",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请用中文描述这个电影画面中发生了什么。注意：1) 识别主要人物 2) 描述场景和环境 3) 分析人物情绪 4) 推测可能的剧情发展。直接输出描述，不要加序号。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
            
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2, 4, 6, 8 秒递增
                print(f"  访问限流，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise e

def analyze_frames_batch(frame_paths: list, sample_rate: float = 0.3, delay=3) -> list:
    """
    批量分析帧，sample_rate 是采样率（避免token消耗过快）
    返回每个帧的描述列表
    """
    import math
    total = len(frame_paths)
    sample_count = max(1, math.ceil(total * sample_rate))
    step = total // sample_count
    
    sampled_frames = frame_paths[::step] if step > 0 else frame_paths[:sample_count]
    
    descriptions = []
    for i, frame_path in enumerate(sampled_frames):
        print(f"分析帧 {i+1}/{len(sampled_frames)}: {frame_path}")
        desc = analyze_single_frame(frame_path)
        descriptions.append(desc)

        # 每帧之间强制等待3秒，避免触发限流
        if i < len(sampled_frames) - 1:
            time.sleep(delay)
    
    return descriptions
