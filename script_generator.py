import time

import os
from config import SCRIPTS_DIR
from openai import OpenAI, RateLimitError
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def generate_script(movie_name: str, frame_descriptions: list, style: str = "悬疑", max_retries=10) -> str:
    """
    基于帧描述生成解说文案
    style: 悬疑 / 喜剧 / 热血 / 温情
    """
    if not frame_descriptions:
        raise Exception("帧描述列表为空，无法生成文案")

    print(f"[DEBUG] 传入的 frame_descriptions 数量: {len(frame_descriptions)}")
    print(f"[DEBUG] 第一条描述: {frame_descriptions[0][:100] if frame_descriptions else '空'}")
    
    descriptions_text = "\n\n".join([
        f"【场景{i+1}】{desc}" for i, desc in enumerate(frame_descriptions)
    ])
    
    prompt = f"""
你是一个专业的影视解说博主，擅长用{style}风格解说电影。

电影名称：《{movie_name}》

以下是对电影关键画面的分析：
{descriptions_text}

请写一段3分钟左右的解说文案，要求：
1. 开头用悬念制造钩子，吸引观众继续看
2. 按照剧情发展顺序讲解，有起承转合
3. 语言口语化，节奏感强，适合配音
4. 适当加入吐槽、金句或情绪表达
5. 结尾用开放式问题引导观众评论（如"你觉得主角做得对吗？评论区告诉我"）

直接输出文案，不要加任何解释和序号。
"""
    
    for attempt in range(max_retries):
        try:
            #print(f"  调用 API 生成文案 (尝试 {attempt + 1}/{max_retries})...")
            response = client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=2000
            )
            script = response.choices[0].message.content
            
            if not script or len(script.strip()) == 0:
                raise Exception("生成的文案为空")
            
            print(f"  文案生成成功，长度：{len(script)} 字符")
            return script
            
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3  # 3, 6, 9, 12 秒
                print(f"  文案生成限流，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise e
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 5
                print(f"  生成失败：{e}，{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                raise Exception(f"文案生成失败：{e}")
    raise Exception("文案生成失败，已达最大重试次数")

def save_script(script: str, movie_name: str) -> str:
    """保存文案到文件"""
    
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    output_path = os.path.join(SCRIPTS_DIR, f"{movie_name}_script.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(script)
    
    # 验证文件已写入
    if os.path.getsize(output_path) == 0:
        raise Exception(f"文案文件保存失败：{output_path} 为空")

    return output_path

def generate_script_by_scenes(movie_name: str, scene_analyses: list, style: str = "悬疑", max_retries=10) -> list:
    """为每个场景生成解说词"""
    
    if not scene_analyses:
        raise ValueError("场景分析列表为空，无法生成文案")
    
    # 构建场景描述
    scenes_text = "\n".join([
        f"[{a['time_str']}] 场景{a['scene_id']+1}: {a['description']}"
        for a in scene_analyses
    ])
    
    prompt = f"""
你是{style}风格的解说博主。

电影《{movie_name}》的场景分析：
{scenes_text}

请为每个场景生成一句解说词。
输出格式（每行）：
[时间] 解说词

要求：
1. 解说词要与场景内容匹配
2. 语言口语化，有感染力
3. 直接输出，不要解释
"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            
            # 验证响应格式
            if not response.choices or len(response.choices) == 0:
                raise Exception("API返回的响应中没有choices")
            
            if not response.choices[0].message or not response.choices[0].message.content:
                raise Exception("API返回的响应中没有message.content")
            
            content = response.choices[0].message.content
            
            # 解析并合并场景信息
            segments = []
            lines = content.strip().split('\n')
            
            for i, line in enumerate(lines):
                if line.startswith('[') and i < len(scene_analyses):
                    time_str = line.split(']')[0][1:]
                    text = line.split(']')[1].strip()
                    segments.append({
                        'scene_id': i,
                        'time_str': time_str,
                        'text': text,
                        'start': scene_analyses[i]['start'],
                        'end': scene_analyses[i]['end']
                    })
            
            if len(segments) != len(scene_analyses):
                print(f"  警告：生成的解说词数量({len(segments)})与场景数量({len(scene_analyses)})不匹配")
            
            return segments
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3  # 3, 6, 9, 12 秒
                print(f"  文案生成限流，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise e
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 5
                print(f"  生成失败：{e}，{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                raise Exception(f"文案生成失败：{e}")
    raise Exception("文案生成失败，已达最大重试次数")
    