"""
批量修图工具（Batch Retoucher）
基于Pillow，支持人像磨皮、美白、锐化、降噪、色彩增强等常见修图操作
适用于视频制作中的素材预处理、头像美化、产品图修图等场景
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# ============ 修图风格预设 ============
RETOUCH_PRESETS = {
    "portrait_soft": {
        "name": "人像柔焦",
        "description": "柔和磨皮+轻微美白+自然锐化，适合人像",
        "smooth": 0.3, "whiten": 0.15, "sharpen": 0.2,
        "brightness": 1.05, "contrast": 1.05, "saturation": 1.05,
    },
    "portrait_glam": {
        "name": "人像精修",
        "description": "深度磨皮+美白+高锐化，适合商业人像",
        "smooth": 0.5, "whiten": 0.25, "sharpen": 0.4,
        "brightness": 1.1, "contrast": 1.1, "saturation": 1.1,
    },
    "product_crisp": {
        "name": "产品清晰",
        "description": "高锐化+高对比+色彩增强，适合产品图",
        "smooth": 0.0, "whiten": 0.0, "sharpen": 0.5,
        "brightness": 1.0, "contrast": 1.15, "saturation": 1.15,
    },
    "landscape_vivid": {
        "name": "风景鲜艳",
        "description": "高饱和+高对比+轻微锐化，适合风景",
        "smooth": 0.0, "whiten": 0.0, "sharpen": 0.3,
        "brightness": 1.05, "contrast": 1.1, "saturation": 1.25,
    },
    "film_warm": {
        "name": "胶片暖色",
        "description": "暖色调+低饱和+轻微颗粒，复古胶片感",
        "smooth": 0.1, "whiten": 0.0, "sharpen": 0.1,
        "brightness": 1.0, "contrast": 1.05, "saturation": 0.9,
        "warmth": 0.15,
    },
    "clean_minimal": {
        "name": "干净极简",
        "description": "轻微提亮+低饱和+自然锐化，干净通透",
        "smooth": 0.1, "whiten": 0.05, "sharpen": 0.2,
        "brightness": 1.08, "contrast": 1.0, "saturation": 0.95,
    },
}


@dataclass
class RetouchConfig:
    """修图配置"""
    smooth: float = 0.0          # 磨皮强度 0-1
    whiten: float = 0.0          # 美白强度 0-1
    sharpen: float = 0.0         # 锐化强度 0-1
    brightness: float = 1.0      # 亮度 0.5-2.0
    contrast: float = 1.0        # 对比度 0.5-2.0
    saturation: float = 1.0      # 饱和度 0.5-2.0
    warmth: float = 0.0          # 暖色调 -1到1（正=暖，负=冷）
    denoise: float = 0.0         # 降噪强度 0-1
    vignette: float = 0.0        # 暗角强度 0-1

    @classmethod
    def from_preset(cls, preset_name: str) -> "RetouchConfig":
        """从预设创建配置"""
        preset = RETOUCH_PRESETS.get(preset_name)
        if not preset:
            logger.warning(f"预设不存在: {preset_name}，使用默认配置")
            return cls()
        return cls(**{k: v for k, v in preset.items()
                      if k in cls.__dataclass_fields__})


class BatchRetoucher:
    """批量修图工具"""

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)

    def retouch_image(self, input_path: str, output_path: str = None,
                      config: RetouchConfig = None,
                      preset: str = None) -> Optional[str]:
        """
        对单张图片进行修图

        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径（None则自动生成）
            config: 修图配置
            preset: 预设名称（优先使用config）

        Returns:
            输出图片路径，失败返回None
        """
        if not _PIL_AVAILABLE:
            logger.error("Pillow未安装，无法修图")
            return None

        if not os.path.exists(input_path):
            logger.error(f"图片不存在: {input_path}")
            return None

        # 确定配置
        if config is None:
            config = RetouchConfig.from_preset(preset) if preset else RetouchConfig()

        # 确定输出路径
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_retouched{ext}"
        if self.output_dir:
            output_path = os.path.join(self.output_dir, os.path.basename(output_path))

        try:
            img = Image.open(input_path).convert("RGB")
            original_size = img.size

            # 1. 磨皮（双边模糊模拟）
            if config.smooth > 0:
                smooth_radius = config.smooth * 5
                blurred = img.filter(ImageFilter.GaussianBlur(radius=smooth_radius))
                # 混合原图和模糊图（保留边缘）
                img = Image.blend(img, blurred, config.smooth * 0.5)

            # 2. 美白（提升亮度+降低饱和度的红色通道）
            if config.whiten > 0:
                r, g, b = img.split()
                r = r.point(lambda x: min(255, int(x + config.whiten * 30)))
                g = g.point(lambda x: min(255, int(x + config.whiten * 20)))
                b = b.point(lambda x: min(255, int(x + config.whiten * 15)))
                img = Image.merge("RGB", (r, g, b))

            # 3. 降噪
            if config.denoise > 0:
                img = img.filter(ImageFilter.MedianFilter(size=3))

            # 4. 亮度
            if config.brightness != 1.0:
                img = ImageEnhance.Brightness(img).enhance(config.brightness)

            # 5. 对比度
            if config.contrast != 1.0:
                img = ImageEnhance.Contrast(img).enhance(config.contrast)

            # 6. 饱和度
            if config.saturation != 1.0:
                img = ImageEnhance.Color(img).enhance(config.saturation)

            # 7. 暖色调
            if config.warmth != 0:
                r, g, b = img.split()
                warm_amount = int(config.warmth * 30)
                r = r.point(lambda x: min(255, max(0, x + warm_amount)))
                b = b.point(lambda x: min(255, max(0, x - warm_amount)))
                img = Image.merge("RGB", (r, g, b))

            # 8. 锐化（最后做，避免放大噪点）
            if config.sharpen > 0:
                sharpened = img.filter(ImageFilter.UnsharpMask(
                    radius=2, percent=int(config.sharpen * 150), threshold=3
                ))
                img = Image.blend(img, sharpened, config.sharpen)

            # 9. 暗角
            if config.vignette > 0:
                img = self._apply_vignette(img, config.vignette)

            # 保存
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path, quality=95)
            logger.info(f"修图完成: {os.path.basename(input_path)} → {os.path.basename(output_path)}")
            return output_path

        except Exception as e:
            logger.error(f"修图失败: {input_path} - {e}")
            return None

    def _apply_vignette(self, img: Image.Image, intensity: float) -> Image.Image:
        """应用暗角效果"""
        width, height = img.size
        # 创建暗角蒙版
        vignette = Image.new("L", (width, height), 255)
        pixels = vignette.load()
        center_x, center_y = width // 2, height // 2
        max_dist = (center_x ** 2 + center_y ** 2) ** 0.5

        for y in range(height):
            for x in range(width):
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                factor = 1 - (dist / max_dist) * intensity
                pixels[x, y] = int(255 * max(0, factor))

        # 应用暗角
        dark = Image.new("RGB", (width, height), (0, 0, 0))
        img = Image.composite(img, dark, vignette)
        return img

    def batch_retouch(self, input_paths: List[str], output_dir: str = None,
                      config: RetouchConfig = None, preset: str = None) -> List[Dict]:
        """
        批量修图

        Args:
            input_paths: 输入图片路径列表
            output_dir: 输出目录
            config: 修图配置
            preset: 预设名称

        Returns:
            结果列表，每个元素：{"input": ..., "output": ..., "success": bool}
        """
        results = []
        for input_path in input_paths:
            output_path = None
            if output_dir:
                base = os.path.basename(input_path)
                name, ext = os.path.splitext(base)
                output_path = os.path.join(output_dir, f"{name}_retouched{ext}")

            result = self.retouch_image(input_path, output_path, config, preset)
            results.append({
                "input": input_path,
                "output": result,
                "success": result is not None,
            })

        success_count = sum(1 for r in results if r["success"])
        logger.info(f"批量修图完成: {success_count}/{len(results)}成功")
        return results

    def compare_before_after(self, input_path: str, output_path: str = None,
                             config: RetouchConfig = None,
                             preset: str = None) -> Optional[str]:
        """
        生成修图前后对比图（左右拼接）

        Args:
            input_path: 输入图片路径
            output_path: 输出对比图路径
            config: 修图配置
            preset: 预设名称

        Returns:
            对比图路径
        """
        if not _PIL_AVAILABLE:
            return None

        # 先修图
        retouched_path = self.retouch_image(input_path, None, config, preset)
        if not retouched_path:
            return None

        # 拼接对比图
        original = Image.open(input_path).convert("RGB")
        retouched = Image.open(retouched_path).convert("RGB")

        width = original.width + retouched.width
        height = max(original.height, retouched.height)
        comparison = Image.new("RGB", (width, height), (255, 255, 255))
        comparison.paste(original, (0, 0))
        comparison.paste(retouched, (original.width, 0))

        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_comparison{ext}"

        comparison.save(output_path, quality=95)
        logger.info(f"对比图生成: {output_path}")
        return output_path

    def list_presets(self) -> List[Dict]:
        """列出所有修图预设"""
        return [
            {"name": name, "description": preset["description"]}
            for name, preset in RETOUCH_PRESETS.items()
        ]


# ============ 便捷函数 ============
def retouch_with_preset(input_path: str, preset_name: str,
                        output_path: str = None) -> Optional[str]:
    """使用预设修图（便捷函数）"""
    retoucher = BatchRetoucher()
    return retoucher.retouch_image(input_path, output_path, preset=preset_name)


def batch_retouch_with_preset(input_paths: List[str], preset_name: str,
                              output_dir: str = None) -> List[Dict]:
    """批量使用预设修图（便捷函数）"""
    retoucher = BatchRetoucher(output_dir)
    return retoucher.batch_retouch(input_paths, output_dir, preset=preset_name)


if __name__ == "__main__":
    # 自测
    retoucher = BatchRetoucher()
    print("可用预设:")
    for p in retoucher.list_presets():
        print(f"  - {p['name']}: {p['description']}")
    print("\n✅ BatchRetoucher模块加载成功")
