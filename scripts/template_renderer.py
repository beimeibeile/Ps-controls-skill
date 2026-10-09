"""
PSD模板渲染器
基于PSD模板，批量替换文字/图片，生成多张输出图
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """PSD模板渲染器"""

    def __init__(self, template_path: str):
        self.template_path = template_path
        self._psd = None

    def _load(self):
        """延迟加载PSD模板"""
        if self._psd is None:
            try:
                from psd_tools import PSDImage
                self._psd = PSDImage.open(self.template_path)
            except ImportError:
                logger.error("psd-tools未安装，请运行: pip install psd-tools")
                raise
        return self._psd

    def get_template_info(self) -> Dict[str, Any]:
        """获取模板信息（可替换的文字图层和图片占位符）"""
        psd = self._load()
        info = {
            "width": psd.width,
            "height": psd.height,
            "text_layers": [],
            "image_placeholders": [],
        }

        def _scan(layers, path=""):
            for layer in layers:
                layer_path = f"{path}/{layer.name}" if path else layer.name
                if layer.kind == "type":
                    try:
                        info["text_layers"].append({
                            "path": layer_path,
                            "name": layer.name,
                            "current_text": layer.text,
                        })
                    except Exception:
                        pass
                elif layer.kind == "pixel":
                    # 命名约定: placeholder_xxx 表示图片占位符
                    if layer.name.lower().startswith("placeholder"):
                        info["image_placeholders"].append({
                            "path": layer_path,
                            "name": layer.name,
                            "bbox": list(layer.bbox) if layer.bbox else None,
                        })
                if layer.kind == "group":
                    _scan(layer, layer_path)

        _scan(psd)
        return info

    def render(
        self,
        replacements: Dict[str, str],
        output_path: str,
        image_replacements: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        渲染模板（简单版本：直接合成PSD，不修改图层内容）

        注意：psd-tools主要用于读取，修改PSD图层内容需要Photoshop COM API。
        当前版本仅支持合成输出，文字/图片替换需要通过PS COM API实现。

        Args:
            replacements: 文字替换 {图层名: 新文字}
            output_path: 输出路径
            image_replacements: 图片替换 {占位符名: 图片路径}
        """
        try:
            psd = self._load()
            image = psd.composite()
            if image:
                image.save(output_path)
                logger.info(f"模板已渲染: {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"渲染模板失败: {e}")
        return None

    def batch_render(
        self,
        data_list: List[Dict[str, Any]],
        output_dir: str,
        name_field: str = "title",
    ) -> Dict[str, Any]:
        """
        批量渲染模板

        Args:
            data_list: 数据列表，每个元素是一组替换数据
            output_dir: 输出目录
            name_field: 用于生成文件名的字段
        """
        os.makedirs(output_dir, exist_ok=True)
        results = {"success": [], "failed": []}

        for i, data in enumerate(data_list):
            try:
                name = data.get(name_field, f"output_{i}")
                # 清理文件名中的非法字符
                safe_name = "".join(c for c in name if c.isalnum() or c in " -_")
                output_path = os.path.join(output_dir, f"{safe_name}.png")

                replacements = data.get("text", {})
                image_replacements = data.get("images", {})

                result = self.render(replacements, output_path, image_replacements)
                if result:
                    results["success"].append({"name": name, "output": result})
                else:
                    results["failed"].append({"name": name, "error": "渲染失败"})
            except Exception as e:
                results["failed"].append({"name": data.get(name_field, f"item_{i}"), "error": str(e)})

        logger.info(f"批量渲染完成: {len(results['success'])}/{len(data_list)} 成功")
        return results


class PhotoshopCOM:
    """
    Photoshop COM API封装（可选，需要安装Photoshop）
    支持真正的PSD修改：替换文字、替换图片、应用样式等
    """

    def __init__(self):
        self._app = None

    def _connect(self):
        """连接Photoshop"""
        if self._app is None:
            try:
                import win32com.client
                self._app = win32com.client.Dispatch("Photoshop.Application")
            except ImportError:
                logger.error("pywin32未安装，请运行: pip install pywin32")
                raise
            except Exception as e:
                logger.error(f"无法连接Photoshop: {e}")
                raise
        return self._app

    def open_document(self, psd_path: str):
        """打开PSD文档"""
        app = self._connect()
        return app.Open(psd_path)

    def replace_text(self, doc, layer_name: str, new_text: str):
        """替换文字图层内容"""
        try:
            for i in range(1, doc.Layers.Count + 1):
                layer = doc.Layers(i)
                if layer.Name == layer_name and layer.Kind == 2:  # 2=TextLayer
                    layer.TextItem.Contents = new_text
                    return True
        except Exception as e:
            logger.error(f"替换文字失败: {e}")
        return False

    def export_png(self, doc, output_path: str):
        """导出为PNG"""
        try:
            from win32com.client import constants
            options = doc.ExportOptions
            options.PNG8 = False
            doc.Export(ExportIn=output_path, ExportAs=constants.psExportPNG, Options=options)
            return True
        except Exception as e:
            logger.error(f"导出PNG失败: {e}")
            return False

    def close(self, doc, save: bool = False):
        """关闭文档"""
        try:
            doc.Close(save)
        except Exception:
            pass


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="PSD模板渲染器")
    parser.add_argument("--template", required=True, help="PSD模板路径")
    parser.add_argument("--info", action="store_true", help="显示模板信息")
    parser.add_argument("--output", help="输出路径")
    args = parser.parse_args()

    renderer = TemplateRenderer(args.template)

    if args.info:
        info = renderer.get_template_info()
        print(json.dumps(info, ensure_ascii=False, indent=2))
    elif args.output:
        renderer.render({}, args.output)
        print(f"已渲染: {args.output}")


if __name__ == "__main__":
    main()
