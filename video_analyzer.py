import base64
import time
import json
from openai import OpenAI
from config import ZHIPU_API_KEY, ZHIPU_BASE_URL, SCRIPTS_DIR

client = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL)

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def analyze_scenes(frames: list, movie_name: str, max_retries: int = 6) -> list:
    """分析所有场景画面"""
    analyses = []
    
    for i, frame in enumerate(frames):
        print(f"  分析场景 {i+1}/{len(frames)}: {frame['time_str']}")
        
        base64_image = encode_image(frame['path'])
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="glm-4.6v-flash",
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"这是视频 {frame['time_str']} 的画面。请用一句话描述：正在发生什么？"
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            }
                        ]
                    }],
                    temperature=0.7,
                    max_tokens=200
                )
                
                analyses.append({
                    'scene_index': frame['scene_index'],
                    'timestamp': frame['timestamp'],
                    'time_str': frame['time_str'],
                    'description': response.choices[0].message.content
                })
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"    限流，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"    分析失败: {e}")
                    analyses.append({
                        'scene_index': frame['scene_index'],
                        'timestamp': frame['timestamp'],
                        'time_str': frame['time_str'],
                        'description': "画面分析失败"
                    })
        
        # 避免限流
        time.sleep(2)
    
    # 保存分析结果
    analyses_path = os.path.join(SCRIPTS_DIR, f"{movie_name}_analyses.json")
    with open(analyses_path, 'w', encoding='utf-8') as f:
        json.dump(analyses, f, indent=2, ensure_ascii=False)
    
    return analyses