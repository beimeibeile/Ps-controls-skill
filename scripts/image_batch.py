"""
图片批处理器
基于Pillow，批量裁剪、缩放、调色、格式转换
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# 支持的图片格式
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".gif"}


class BatchProcessor:
    """图片批处理器"""

    def __init__(self):
        self._pil = None

    def _get_pil(self):
        """延迟导入Pillow"""
        if self._pil is None:
            try:
                from PIL import Image, ImageOps, ImageEnhance
                self._pil = Image
                self._ImageOps = ImageOps
                self._ImageEnhance = ImageEnhance
            except ImportError:
                logger.error("Pillow未安装，请运行: pip install Pillow")
                raise
        return self._pil

    def process(
        self,
        input_dir: str,
        output_dir: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        format: str = "PNG",
        quality: int = 95,
        mode: str = "contain",  # contain / cover / stretch
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
    ) -> Dict[str, Any]:
        """
        批量处理图片

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            width/height: 目标尺寸
            format: 输出格式 (PNG/JPEG/WEBP)
            quality: JPEG质量 (1-100)
            mode: 缩放模式 (contain留白/cover裁剪/stretch拉伸)
            brightness/contrast/saturation: 调色参数 (1.0=原始)
        """
        Image = self._get_pil()
        os.makedirs(output_dir, exist_ok=True)

        # 收集图片文件
        image_files = []
        for f in Path(input_dir).iterdir():
            if f.suffix.lower() in SUPPORTED_FORMATS:
                image_files.append(f)

        results = {"success": [], "failed": [], "total": len(image_files)}

        for img_path in image_files:
            try:
                output_path = os.path.join(
                    output_dir,
                    f"{img_path.stem}.{format.lower()}"
                )
                self._process_single(
                    str(img_path), output_path,
                    width, height, format, quality, mode,
                    brightness, contrast, saturation
                )
                results["success"].append({
                    "input": str(img_path),
                    "output": output_path,
                })
                logger.info(f"处理成功: {img_path.name}")
            except Exception as e:
                results["failed"].append({
                    "input": str(img_path),
                    "error": str(e),
                })
                logger.error(f"处理失败 {img_path.name}: {e}")

        logger.info(f"批处理完成: {len(results['success'])}/{results['total']} 成功")
        return results

    def _process_single(
        self, input_path: str, output_path: str,
        width: Optional[int], height: Optional[int],
        format: str, quality: int, mode: str,
        brightness: float, contrast: float, saturation: float,
    ):
        """处理单张图片"""
        Image = self._get_pil()
        img = Image.open(input_path)

        # 转换为RGB（处理透明通道）
        if img.mode in ("RGBA", "P"):
            if format.upper() == "JPEG":
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = bg
            else:
                img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        # 缩放
        if width and height:
            img = self._resize(img, width, height, mode)

        # 调色
        if brightness != 1.0:
            img = self._ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = self._ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = self._ImageEnhance.Color(img).enhance(saturation)

        # 保存
        save_kwargs = {}
        if format.upper() == "JPEG":
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif format.upper() == "WEBP":
            save_kwargs["quality"] = quality

        img.save(output_path, format.upper(), **save_kwargs)

    def _resize(self, img, width: int, height: int, mode: str):
        """按模式缩放图片"""
        Image = self._get_pil()
        src_w, src_h = img.size

        if mode == "stretch":
            return img.resize((width, height), Image.LANCZOS)
        elif mode == "cover":
            # 裁剪填充
            scale = max(width / src_w, height / src_h)
            new_w, new_h = int(src_w * scale), int(src_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - width) // 2
            top = (new_h - height) // 2
            return img.crop((left, top, left + width, top + height))
        else:  # contain
            # 等比缩放，留白
            scale = min(width / src_w, height / src_h)
            new_w, new_h = int(src_w * scale), int(src_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            # 创建画布
            mode_canvas = "RGBA" if "A" in img.getbands() else "RGB"
            canvas = Image.new(mode_canvas, (width, height),
                             (0, 0, 0, 0) if mode_canvas == "RGBA" else (0, 0, 0))
            offset = ((width - new_w) // 2, (height - new_h) // 2)
            canvas.paste(img, offset)
            return canvas

    def create_cover(
        self,
        background: str,
        title: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920,
        title_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Optional[str]:
        """
        生成视频封面（背景+标题）
        简单版本，复杂排版建议使用PSD模板
        """
        try:
            Image = self._get_pil()
            from PIL import ImageDraw, ImageFont

            # 背景
            if os.path.exists(background):
                bg = Image.open(background).convert("RGB")
                bg = self._resize(bg, width, height, "cover")
            else:
                bg = Image.new("RGB", (width, height), (30, 30, 40))

            # 标题
            draw = ImageDraw.Draw(bg)
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except Exception:
                font = ImageFont.load_default()

            # 居中绘制标题
            bbox = draw.textbbox((0, 0), title, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (width - text_w) // 2
            y = (height - text_h) // 2
            draw.text((x, y), title, fill=title_color, font=font)

            bg.save(output_path, "JPEG", quality=95)
            logger.info(f"封面已生成: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"生成封面失败: {e}")
            return None


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="图片批处理器")
    parser.add_argument("--input", required=True, help="输入目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--width", type=int, help="目标宽度")
    parser.add_argument("--height", type=int, help="目标高度")
    parser.add_argument("--format", default="PNG", help="输出格式")
    parser.add_argument("--mode", default="contain", choices=["contain", "cover", "stretch"])
    args = parser.parse_args()

    processor = BatchProcessor()
    results = processor.process(
        input_dir=args.input,
        output_dir=args.output,
        width=args.width,
        height=args.height,
        format=args.format,
        mode=args.mode,
    )
    print(f"完成: {len(results['success'])}/{results['total']} 成功")


if __name__ == "__main__":
    main()
