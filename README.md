# Ps Controls Skill

> Photoshop 智能管理与控制框架 —— PSD解析 + 批量处理 + 模板渲染 + 封面生成，全链路自动化。

## 姊妹项目

| 项目 | 定位 |
|------|------|
| **ai-video-editor** | AI视频剪辑框架（大脑/集成平台） |
| **jianying-editor** | 剪映工程控制 |
| **Pr-controls-skill** | Pr工程控制 |
| **Ps-controls-skill** | Photoshop控制（本项目） |
| **Comfyui-controls-skill** | ComfyUI智能管理 |
| **Blender-controls-skill** | Blender智能管理 |
| **remotion-controls-skill** | Remotion代码动画 |
| **anysearch-skill** | 深度搜索 |

## 核心能力

- **PSD解析** — 读取PSD图层结构、文字、样式，导出JSON
- **图片批处理** — 批量裁剪、缩放、调色、格式转换
- **模板渲染** — PSD模板批量替换文字/图片
- **封面生成** — 自动化生成视频封面、海报

## 快速开始

```bash
# 安装依赖
pip install psd-tools Pillow

# 解析PSD
python scripts/psd_parser.py input.psd -o output.json

# 批量处理图片
python scripts/image_batch.py --input ./images --output ./output --width 1080 --height 1920
```

## 项目架构

```
Ps-controls-skill/
├── capabilities/              # 能力模块
│   ├── cap_psd_parser/
│   └── cap_batch_processor/
├── scripts/                   # 工具脚本
│   ├── paths.py
│   ├── psd_parser.py
│   ├── image_batch.py
│   └── template_renderer.py
├── templates/                 # PSD模板库
├── tests/                     # 测试
├── SKILL.md
└── README.md
```

## License

MIT
