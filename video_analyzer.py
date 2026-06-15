import base64
import time
from openai import OpenAI, RateLimitError
from config import ZHIPU_API_KEY, ZHIPU_BASE_URL

client = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL)

def encode_image(image_path: str) -> str:
    """将图片编码为base64"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    except Exception as e:
        raise Exception(f"编码图片失败: {str(e)}")

def analyze_single_frame(frame_path: str, max_retries=5) -> str:
    """分析单张关键帧，带自动重试"""    
    base64_image = encode_image(frame_path)
    
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
            
            # 验证响应格式
            if not response.choices or len(response.choices) == 0:
                raise Exception("API返回的响应中没有choices")
            
            if not response.choices[0].message or not response.choices[0].message.content:
                raise Exception("API返回的响应中没有message.content")
            
            return response.choices[0].message.content
            
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2, 4, 6, 8 秒递增
                print(f"  访问限流，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise e
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"  分析失败，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(wait_time)
            else:
                raise e

def analyze_scene_batch(scenes: list, frame_paths: list) -> list:
    """批量分析场景，返回带场景信息的分析结果"""
    if not scenes or not frame_paths:
        raise ValueError("scenes和frame_paths不能为空")
    
    if len(scenes) != len(frame_paths):
        raise ValueError(f"scenes数量({len(scenes)})与frame_paths数量({len(frame_paths)})不匹配")
    
    analyses = []
    
    for i, (scene, frame_path) in enumerate(zip(scenes, frame_paths)):
        print(f"  进行第{i+1}个场景的分析...")
        desc = analyze_single_frame(frame_path['path'])
                       
        analyses.append({
            'scene_id': i,
            'start': scene['start'],
            'end': scene['end'],
            'time_str': frame_path['time_str'],
            'description': desc
        })
        
        # 添加延迟以避免API限流
        if i < len(scenes) - 1:  # 最后一个场景不需要延迟
            time.sleep(2)  # 每次分析后等待2秒
    
    return analyses
