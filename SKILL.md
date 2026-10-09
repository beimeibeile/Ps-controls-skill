---
name: Ps-controls-skill
version: 1.0.0
description: |
  Photoshop智能管理与控制技能。核心能力：PSD解析/生成、图片批处理、
  模板化设计、海报/封面自动生成。与ai-video-editor、jianying-editor、
  Pr-controls-skill等为姊妹项目，可独立工作也可挂载协同。
  Use when asked to 处理PSD、批量图片、PS自动化、海报生成、图片预处理、抠图、调色。
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
triggers:
  - ps
  - photoshop
  - PSD
  - 批处理
  - 海报生成
  - 图片预处理
  - ps控制
  - ps管理
metadata:
  license: MIT
  requires:
    bins:
      - python
      - git
    optional:
      - Photoshop (COM API)
      - ImageMagick
---

# Ps Controls Skill

> **Photoshop 智能管理与控制框架** —— 让 PS 从工具变成自动出图的智能体。PSD解析 + 批量处理 + 模板渲染 + 封面生成，全链路自动化。

## 姊妹项目（航空母舰战斗群）

| 项目 | 定位 | 角色 |
|------|------|------|
| **ai-video-editor** | AI视频剪辑框架 | 🚢 航空母舰（大脑/集成平台） |
| **jianying-editor** | 剪映工程控制 | ✂️ 剪刀手（剪辑合成） |
| **Pr-controls-skill** | Pr工程控制 | 🎬 剪辑师（Pr工程） |
| **Ps-controls-skill** | Photoshop控制（本项目） | 🎨 设计师（图像处理） |
| **Comfyui-controls-skill** | ComfyUI智能管理 | 🚀 AI算力（生成/抠图） |
| **Blender-controls-skill** | Blender智能管理 | 🧊 3D特效师 |
| **remotion-controls-skill** | Remotion代码动画 | 🎭 动画师 |
| **anysearch-skill** | 深度搜索 | 📡 雷达（情报搜索） |

> 单体都能干活，任意组合互相增强，聚齐就是航空母舰！

## 核心能力

| 能力 | 说明 | 状态 |
|------|------|------|
| **PSD解析** | 读取PSD图层结构、文字、样式，导出JSON | ✅ |
| **图片批处理** | 批量裁剪、缩放、调色、格式转换 | ✅ |
| **模板渲染** | PSD模板批量替换文字/图片 | 🚧 |
| **封面生成** | 自动化生成视频封面、海报 | 🚧 |
| **PS COM API** | 调用Photoshop完整功能 | ⏳ 可选 |
| **抠图/调色** | 基于Pillow的基础图像处理 | ✅ |

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/beimeibeile/Ps-controls-skill.git
cd Ps-controls-skill

# 2. 安装依赖
pip install psd-tools Pillow

# 3. 解析PSD
python scripts/psd_parser.py input.psd output.json

# 4. 批量处理图片
python scripts/image_batch.py --input ./images --output ./output --width 1080 --height 1920
```

## 环境要求

| 组件 | 必需？ | 说明 |
|------|--------|------|
| **Python** | ✅ 必需 | ≥ 3.10 |
| **psd-tools** | ✅ 必需 | PSD解析 |
| **Pillow** | ✅ 必需 | 图片处理 |
| **Photoshop** | ⚡ 可选 | COM API高级功能 |
| **ImageMagick** | 可选 | 高级批处理 |

## 项目架构

```
Ps-controls-skill/
├── capabilities/              # 能力模块（可插拔）
│   ├── cap_psd_parser/           # PSD解析
│   └── cap_batch_processor/      # 批量处理
├── scripts/                   # 工具脚本
│   ├── paths.py                   # 统一路径配置
│   ├── psd_parser.py              # PSD文件解析
│   ├── image_batch.py             # 图片批处理
│   └── template_renderer.py       # 模板渲染
├── templates/                 # PSD模板库
├── tests/                     # 测试
├── SKILL.md                   # 本文件
└── README.md                  # 项目说明
```

## 使用示例

### 1. 解析PSD文件

```python
from psd_parser import PSDParser

parser = PSDParser("design.psd")
info = parser.parse()
print(f"图层数: {len(info['layers'])}")
print(f"尺寸: {info['width']}x{info['height']}")
```

### 2. 批量处理图片

```python
from image_batch import BatchProcessor

processor = BatchProcessor()
results = processor.process(
    input_dir="./images",
    output_dir="./output",
    width=1080,
    height=1920,
    format="PNG"
)
print(f"处理完成: {len(results['success'])}成功")
```

## 在视频pipeline中的位置

```
剧本/分镜 → 素材生成(ComfyUI) → 素材预处理(Ps) → 剪辑合成(剪映/Pr) → 输出
                              ↑
                        Ps-controls-skill
                  批量裁剪/调色/抠图/封面生成
```

## License

[MIT](LICENSE)
