import json
import os
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, SCRIPTS_DIR

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def generate_scripts(analyses: list, scenes: list, style: str, movie_name: str) -> list:
    """为每个场景生成解说词"""
    scripts = []
    
    for i, analysis in enumerate(analyses):
        scene = next((item for item in scenes if item["index"] == analysis['scene_index']), None)
        max_chars = int(scene['duration'] * 4)  # 每秒4个字符
        
        prompt = f"""
你是{style}风格的解说博主。

场景内容：{analysis['description']}
场景时长：{scene['duration']:.1f}秒

请生成一句解说词（{max_chars}字以内），直接输出解说词：
"""
        
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=500
        )
        
        script = response.choices[0].message.content.strip()
        
        scripts.append({
            'scene_index': analysis['scene_index'],
            'timestamp': analysis['timestamp'],
            'time_str': analysis['time_str'],
            'description': analysis['description'],
            'script': script,
            'duration': scene['duration']
        })
        
        print(f"  场景{i+1}: {script[:50]}...")
    
    # 保存文案
    scripts_path = os.path.join(SCRIPTS_DIR, f"{movie_name}_scripts.json")
    with open(scripts_path, 'w', encoding='utf-8') as f:
        json.dump(scripts, f, indent=2, ensure_ascii=False)
    
    # 保存纯文本版本
    text_path = os.path.join(SCRIPTS_DIR, f"{movie_name}_script.txt")
    with open(text_path, 'w', encoding='utf-8') as f:
        for script in scripts:
            f.write(f"[{script['time_str']}] {script['script']}\n\n")
    
    return scripts