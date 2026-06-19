# VideoCreater 项目结构（LangChain 重构后）

## 顶层文件

```
VideoCreater/
├── main.py                    # 命令行入口（使用新 Pipeline）
├── app.py                     # Web 界面入口（使用新 Pipeline）
├── app_queue.py               # Celery 批量任务 Web 界面
├── tasks.py                   # Celery 异步任务（使用新 Pipeline）
├── config.py                  # 配置管理
├── requirements.txt           # Python 依赖
├── .env                       # 环境变量（API 密钥）
├── .gitignore                 # Git 忽略配置
├── test_langchain.py          # LangChain 重构验证测试
├── test.py                    # Edge TTS 测试脚本
└── README.md                  # 项目说明（待更新）
```

## 核心架构

### core/ - 核心业务逻辑层（LangChain）

```
core/
├── models/                    # 模型配置
│   ├── __init__.py
│   └── model_config.py        # LLM 模型工厂（智谱/DeepSeek）
├── prompts/                   # Prompt 模板
│   └── __init__.py            # 所有 Prompt 模板定义
├── chains/                    # LangChain Chains
│   ├── __init__.py
│   ├── video_analysis_chain.py    # 视频分析 Chain
│   └── script_generation_chain.py # 文案生成 Chain
└── pipeline.py                # 完整 Pipeline 编排
```

### services/ - 服务层（非 AI 逻辑）

```
services/
├── __init__.py
├── video_service.py           # 视频处理（场景检测、关键帧提取）
├── audio_service.py           # 音频处理（TTS 语音合成）
└── composition_service.py     # 视频合成（剪辑、字幕、合成）
```

### tests/ - 测试

```
tests/
└── test_chains.py             # Chains 和服务的单元测试
```

## 配置和输出

```
.gientech/                     # Harness 配置
└── gientech-harness/
    ├── docs/                  # 文档
    │   ├── LangChain 重构总结.md
    │   ├── 代码清理完成.md
    │   └── ...
    └── wiki/                  # Wiki
        ├── LangChain 重构指南.md
        └── ...

inputs/                        # 输入文件目录
outputs/                       # 输出文件目录
├── frames/                    # 关键帧
├── scenes/                    # 场景信息
├── scripts/                   # 解说文案
├── voice/                     # 语音文件
├── subtitles/                 # 字幕文件
└── videos/                    # 最终视频

cache/                         # 缓存目录
temp/                          # 临时文件目录
```

## 模块依赖关系

```
main.py / app.py / tasks.py
    ↓
core/pipeline.py
    ↓
┌─────────────────────────────────────┐
│  core/chains/      │  services/     │
│  - video_analysis  │  - video       │
│  - script_gen      │  - audio       │
│                    │  - composition │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  core/models/      │  core/prompts/ │
│  - model_config    │  - prompts     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  第三方库：LangChain, OpenAI,        │
│  MoviePy, Edge-TTS, PySceneDetect   │
└─────────────────────────────────────┘
```

## 已删除的旧文件

以下文件已被删除，功能迁移到新架构：

- ❌ `frame_extractor.py` → ✅ `services/video_service.py`
- ❌ `video_analyzer.py` → ✅ `core/chains/video_analysis_chain.py`
- ❌ `script_generator.py` → ✅ `core/chains/script_generation_chain.py`
- ❌ `tts_generator.py` → ✅ `services/audio_service.py`
- ❌ `video_composer.py` → ✅ `services/composition_service.py`

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

编辑 `.env` 文件：

```bash
ZHIPU_API_KEY=your_zhipu_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 3. 运行

**命令行模式**:
```bash
python main.py
```

**Web 界面**:
```bash
python app.py
```

**Celery 批量任务**:
```bash
# 启动 Celery Worker
celery -A tasks worker --loglevel=info

# 启动 Web 界面
python app_queue.py
```

## 编程模式使用示例

```python
from core.pipeline import NarrationPipeline

# 创建 Pipeline
pipeline = NarrationPipeline(
    style="悬疑",
    max_scenes=20,
    cache_enabled=True
)

# 执行
result = pipeline.execute(
    video_path="./inputs/test.mp4",
    movie_name="测试视频",
    progress_callback=lambda c, t, m: print(f"{c/t*100:.0f}%: {m}")
)

if result['status'] == 'success':
    print(f"输出：{result['output_path']}")
```

## 验证测试

```bash
python test_langchain.py
```

预期输出：
```
============================================================
LangChain Refactoring Verification Test
============================================================

[1/4] Testing imports...
  OK: Models
  OK: Prompts - Styles: ['悬疑', '热血', '幽默', '温情']
  OK: Chains
  OK: VideoService
  OK: AudioService
  OK: Pipeline

[2/4] Testing Pipeline creation...
  Style: 悬疑
  Max scenes: 20
  Dirs: ['frames', 'scenes', 'scripts', 'voice', 'subtitles', 'videos']
  OK: Pipeline created

[3/4] Testing Chains...
  OK: VideoAnalysisChain
  OK: ScriptGenerationChain

[4/4] Testing Services...
  OK: VideoService
  OK: AudioService

============================================================
ALL TESTS PASSED!
============================================================
```

---

**更新时间**: 2026-06-18
**状态**: LangChain 重构完成，旧代码已清理
