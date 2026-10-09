"""
PSD文件解析器
基于psd-tools库，解析PSD文件结构（图层、组、文字、样式），导出JSON
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PSDParser:
    """PSD文件解析器"""

    def __init__(self, psd_path: str):
        self.psd_path = psd_path
        self._psd = None

    def _load(self):
        """延迟加载PSD文件"""
        if self._psd is None:
            try:
                from psd_tools import PSDImage
                self._psd = PSDImage.open(self.psd_path)
            except ImportError:
                logger.error("psd-tools未安装，请运行: pip install psd-tools")
                raise
            except Exception as e:
                logger.error(f"无法打开PSD文件: {e}")
                raise
        return self._psd

    def parse(self) -> Dict[str, Any]:
        """解析PSD文件，返回结构化信息"""
        psd = self._load()
        result = {
            "file": os.path.basename(self.psd_path),
            "width": psd.width,
            "height": psd.height,
            "mode": str(psd.mode),
            "layers": self._parse_layers(psd),
        }
        return result

    def _parse_layers(self, parent, depth: int = 0) -> List[Dict]:
        """递归解析图层"""
        layers = []
        for layer in parent:
            info = {
                "name": layer.name,
                "kind": layer.kind,
                "visible": layer.visible,
                "opacity": layer.opacity,
                "bbox": list(layer.bbox) if layer.bbox else None,
                "depth": depth,
            }

            # 文字图层额外信息
            if layer.kind == "type":
                try:
                    info["text"] = layer.text
                    info["font_size"] = layer.font_size
                    info["font_name"] = layer.font_name
                except Exception:
                    pass

            # 组图层递归解析子图层
            if layer.kind == "group":
                info["children"] = self._parse_layers(layer, depth + 1)

            layers.append(info)
        return layers

    def export_json(self, output_path: str) -> str:
        """导出解析结果为JSON文件"""
        result = self.parse()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"PSD解析结果已导出: {output_path}")
        return output_path

    def get_text_layers(self) -> List[Dict]:
        """获取所有文字图层"""
        result = self.parse()
        text_layers = []

        def _find_text(layers):
            for layer in layers:
                if layer.get("kind") == "type":
                    text_layers.append(layer)
                if "children" in layer:
                    _find_text(layer["children"])

        _find_text(result["layers"])
        return text_layers

    def render_thumbnail(self, output_path: str, max_size: int = 512) -> Optional[str]:
        """渲染PSD缩略图"""
        try:
            psd = self._load()
            image = psd.composite()
            if image:
                # 等比缩放
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size)
                image.save(output_path)
                logger.info(f"缩略图已保存: {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"渲染缩略图失败: {e}")
        return None


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="PSD文件解析器")
    parser.add_argument("input", help="输入PSD文件路径")
    parser.add_argument("-o", "--output", help="输出JSON文件路径")
    parser.add_argument("-t", "--thumbnail", help="输出缩略图路径")
    args = parser.parse_args()

    psd_parser = PSDParser(args.input)
    result = psd_parser.parse()

    print(f"文件: {result['file']}")
    print(f"尺寸: {result['width']}x{result['height']}")
    print(f"图层数: {len(result['layers'])}")

    if args.output:
        psd_parser.export_json(args.output)
        print(f"已导出: {args.output}")

    if args.thumbnail:
        psd_parser.render_thumbnail(args.thumbnail)
        print(f"缩略图: {args.thumbnail}")


if __name__ == "__main__":
    main()
