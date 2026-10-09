"""
智能调色工具
基于Pillow的图片智能调色，支持多种预设风格和自动调色
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("Pillow未安装，智能调色功能不可用")


class ColorStyle(Enum):
    """调色风格预设"""
    ORIGINAL = "original"              # 原图
    VIVID = "vivid"                    # 鲜艳
    WARM = "warm"                      # 暖色调
    COOL = "cool"                      # 冷色调
    VINTAGE = "vintage"                # 复古
    CINEMATIC = "cinematic"            # 电影感
    BW = "bw"                          # 黑白
    SEPIA = "sepia"                    # 怀旧棕褐
    HDR = "hdr"                        # HDR效果
    SOFT = "soft"                      # 柔和
    SHARP = "sharp"                    # 锐利
    DREAMY = "dreamy"                  # 梦幻
    CYBERPUNK = "cyberpunk"            # 赛博朋克
    FILM = "film"                      # 胶片感


@dataclass
class ColorAdjustParams:
    """调色参数"""
    brightness: float = 1.0      # 亮度 0.0-2.0
    contrast: float = 1.0        # 对比度 0.0-2.0
    saturation: float = 1.0      # 饱和度 0.0-2.0
    sharpness: float = 1.0       # 锐度 0.0-2.0
    hue: float = 0.0             # 色相偏移 -180 to 180
    temperature: float = 0.0     # 色温 -100 to 100 (正=暖, 负=冷)
    tint: float = 0.0            # 色调 -100 to 100 (正=绿, 负=品红)
    vignette: float = 0.0        # 暗角 0.0-1.0
    grain: float = 0.0           # 颗粒 0.0-1.0


# ============ 风格预设参数 ============
STYLE_PRESETS: Dict[ColorStyle, ColorAdjustParams] = {
    ColorStyle.ORIGINAL: ColorAdjustParams(),
    ColorStyle.VIVID: ColorAdjustParams(
        brightness=1.05, contrast=1.15, saturation=1.4, sharpness=1.1
    ),
    ColorStyle.WARM: ColorAdjustParams(
        brightness=1.05, contrast=1.05, saturation=1.1, temperature=30, tint=-5
    ),
    ColorStyle.COOL: ColorAdjustParams(
        brightness=1.0, contrast=1.1, saturation=0.9, temperature=-25, tint=5
    ),
    ColorStyle.VINTAGE: ColorAdjustParams(
        brightness=0.95, contrast=0.9, saturation=0.7, temperature=20, 
        vignette=0.3, grain=0.15
    ),
    ColorStyle.CINEMATIC: ColorAdjustParams(
        brightness=0.9, contrast=1.2, saturation=0.85, temperature=-10,
        vignette=0.4, sharpness=1.05
    ),
    ColorStyle.BW: ColorAdjustParams(
        saturation=0.0, contrast=1.15, brightness=1.0
    ),
    ColorStyle.SEPIA: ColorAdjustParams(
        saturation=0.3, temperature=40, contrast=1.05, brightness=0.95
    ),
    ColorStyle.HDR: ColorAdjustParams(
        brightness=1.1, contrast=1.3, saturation=1.2, sharpness=1.2
    ),
    ColorStyle.SOFT: ColorAdjustParams(
        brightness=1.05, contrast=0.85, saturation=0.9, sharpness=0.7
    ),
    ColorStyle.SHARP: ColorAdjustParams(
        contrast=1.1, sharpness=1.5, saturation=1.05
    ),
    ColorStyle.DREAMY: ColorAdjustParams(
        brightness=1.15, contrast=0.8, saturation=1.1, sharpness=0.6,
        temperature=10, vignette=0.1
    ),
    ColorStyle.CYBERPUNK: ColorAdjustParams(
        brightness=0.95, contrast=1.25, saturation=1.5, temperature=-30,
        tint=15, sharpness=1.1
    ),
    ColorStyle.FILM: ColorAdjustParams(
        brightness=0.98, contrast=1.05, saturation=0.85, temperature=15,
        grain=0.1, vignette=0.2
    ),
}


class SmartColorGrader:
    """
    智能调色器
    
    功能：
    1. 预设风格一键调色
    2. 自定义参数调色
    3. 自动调色（基于图像分析）
    4. 批量调色
    5. 调色前后对比
    """
    
    def __init__(self):
        if not PILLOW_AVAILABLE:
            raise ImportError("Pillow未安装，请先安装: pip install Pillow")
    
    def apply_style(self, image_path: str, style: ColorStyle,
                     output_path: str = None) -> str:
        """
        应用预设风格调色
        
        Args:
            image_path: 输入图片路径
            style: 调色风格
            output_path: 输出路径（默认在原图旁加后缀）
        
        Returns:
            输出文件路径
        """
        params = STYLE_PRESETS.get(style, STYLE_PRESETS[ColorStyle.ORIGINAL])
        return self.apply_adjustments(image_path, params, output_path)
    
    def apply_adjustments(self, image_path: str, 
                           params: ColorAdjustParams,
                           output_path: str = None) -> str:
        """
        应用自定义调色参数
        
        Args:
            image_path: 输入图片路径
            params: 调色参数
            output_path: 输出路径
        
        Returns:
            输出文件路径
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        img = Image.open(image_path)
        
        # 1. 亮度
        if params.brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(params.brightness)
        
        # 2. 对比度
        if params.contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(params.contrast)
        
        # 3. 饱和度
        if params.saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(params.saturation)
        
        # 4. 锐度
        if params.sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(params.sharpness)
        
        # 5. 色温调整
        if params.temperature != 0:
            img = self._adjust_temperature(img, params.temperature)
        
        # 6. 暗角
        if params.vignette > 0:
            img = self._apply_vignette(img, params.vignette)
        
        # 7. 颗粒
        if params.grain > 0:
            img = self._apply_grain(img, params.grain)
        
        # 输出
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_graded{ext}"
        
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        img.save(output_path)
        logger.info("调色完成: %s -> %s", image_path, output_path)
        return output_path
    
    def auto_grade(self, image_path: str, 
                    target_style: str = "balanced",
                    output_path: str = None) -> str:
        """
        自动调色（基于图像分析）
        
        Args:
            image_path: 输入图片路径
            target_style: 目标风格 (balanced/vivid/warm/cool)
            output_path: 输出路径
        
        Returns:
            输出文件路径
        """
        img = Image.open(image_path)
        
        # 分析图像
        analysis = self._analyze_image(img)
        
        # 根据分析结果自动调整
        params = ColorAdjustParams()
        
        # 亮度自动调整
        if analysis["avg_brightness"] < 80:
            params.brightness = 1.2  # 偏暗，提亮
        elif analysis["avg_brightness"] > 200:
            params.brightness = 0.9  # 偏亮，压暗
        
        # 对比度自动调整
        if analysis["contrast"] < 40:
            params.contrast = 1.2  # 低对比，增强
        elif analysis["contrast"] > 80:
            params.contrast = 0.9  # 高对比，降低
        
        # 饱和度自动调整
        if analysis["saturation"] < 30:
            params.saturation = 1.3  # 低饱和，增强
        elif analysis["saturation"] > 80:
            params.saturation = 0.85  # 高饱和，降低
        
        # 目标风格调整
        if target_style == "vivid":
            params.saturation *= 1.3
            params.contrast *= 1.1
        elif target_style == "warm":
            params.temperature = 25
        elif target_style == "cool":
            params.temperature = -20
        
        return self.apply_adjustments(image_path, params, output_path)
    
    def batch_grade(self, image_paths: List[str], 
                     style: ColorStyle,
                     output_dir: str) -> List[str]:
        """
        批量调色
        
        Args:
            image_paths: 图片路径列表
            style: 调色风格
            output_dir: 输出目录
        
        Returns:
            输出文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for img_path in image_paths:
            if not os.path.exists(img_path):
                logger.warning("跳过不存在的文件: %s", img_path)
                continue
            
            filename = os.path.basename(img_path)
            output_path = os.path.join(output_dir, filename)
            result = self.apply_style(img_path, style, output_path)
            results.append(result)
        
        logger.info("批量调色完成: %d/%d", len(results), len(image_paths))
        return results
    
    def create_style_preview(self, image_path: str, 
                              styles: List[ColorStyle] = None,
                              output_path: str = None) -> str:
        """
        创建多风格预览图（横向拼接）
        
        Args:
            image_path: 输入图片
            styles: 要预览的风格列表
            output_path: 输出路径
        
        Returns:
            预览图路径
        """
        if styles is None:
            styles = [
                ColorStyle.ORIGINAL, ColorStyle.VIVID, ColorStyle.WARM,
                ColorStyle.COOL, ColorStyle.CINEMATIC, ColorStyle.BW,
            ]
        
        img = Image.open(image_path)
        thumb_size = (400, int(400 * img.height / img.width))
        
        # 生成各风格缩略图
        thumbnails = []
        for style in styles:
            params = STYLE_PRESETS.get(style, STYLE_PRESETS[ColorStyle.ORIGINAL])
            styled = self._apply_to_image(img.copy(), params)
            styled.thumbnail(thumb_size)
            thumbnails.append((style.value, styled))
        
        # 拼接
        total_width = sum(t[1].width for t in thumbnails)
        max_height = max(t[1].height for t in thumbnails) + 30  # 留标签空间
        
        preview = Image.new("RGB", (total_width, max_height), (255, 255, 255))
        
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(preview)
        
        x_offset = 0
        for name, thumb in thumbnails:
            preview.paste(thumb, (x_offset, 30))
            draw.text((x_offset + 10, 5), name, fill=(0, 0, 0))
            x_offset += thumb.width
        
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_preview{ext}"
        
        preview.save(output_path)
        return output_path
    
    def _analyze_image(self, img: Image.Image) -> Dict[str, float]:
        """分析图像属性"""
        # 转为灰度分析亮度
        gray = img.convert("L")
        pixels = list(gray.getdata())
        avg_brightness = sum(pixels) / len(pixels)
        
        # 对比度（标准差）
        variance = sum((p - avg_brightness) ** 2 for p in pixels) / len(pixels)
        contrast = variance ** 0.5
        
        # 饱和度（简化估算）
        hsv = img.convert("HSV")
        s_pixels = list(hsv.getdata())
        avg_saturation = sum(p[1] for p in s_pixels) / len(s_pixels)
        
        return {
            "avg_brightness": avg_brightness,
            "contrast": contrast,
            "saturation": avg_saturation,
        }
    
    def _adjust_temperature(self, img: Image.Image, 
                             temperature: float) -> Image.Image:
        """调整色温"""
        r, g, b = img.split()
        
        # 暖色：增加红，减少蓝
        if temperature > 0:
            r = r.point(lambda x: min(255, x + temperature * 0.5))
            b = b.point(lambda x: max(0, x - temperature * 0.3))
        # 冷色：增加蓝，减少红
        else:
            r = r.point(lambda x: max(0, x + temperature * 0.3))
            b = b.point(lambda x: min(255, x - temperature * 0.5))
        
        return Image.merge("RGB", (r, g, b))
    
    def _apply_vignette(self, img: Image.Image, 
                         strength: float) -> Image.Image:
        """应用暗角"""
        width, height = img.size
        vignette = Image.new("L", (width, height), 255)
        
        from PIL import ImageDraw
        draw = ImageDraw.Draw(vignette)
        
        # 创建径向渐变暗角
        for i in range(100):
            alpha = int(255 * (1 - strength * (i / 100) ** 2))
            margin = int(min(width, height) * 0.1 * i / 100)
            draw.rectangle(
                [margin, margin, width - margin, height - margin],
                fill=alpha
            )
        
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=50))
        
        # 应用暗角
        black = Image.new("RGB", (width, height), (0, 0, 0))
        img = Image.composite(img, black, vignette)
        return img
    
    def _apply_grain(self, img: Image.Image, 
                      strength: float) -> Image.Image:
        """应用胶片颗粒"""
        import random
        width, height = img.size
        grain = Image.new("L", (width, height))
        
        pixels = grain.load()
        for y in range(height):
            for x in range(width):
                noise = int(random.gauss(128, 30 * strength))
                pixels[x, y] = max(0, min(255, noise))
        
        grain = grain.filter(ImageFilter.GaussianBlur(radius=1))
        
        # 叠加颗粒
        img_array = img.convert("RGB")
        result = Image.blend(img_array, Image.merge("RGB", (grain, grain, grain)), 
                            strength * 0.3)
        return result
    
    def _apply_to_image(self, img: Image.Image, 
                         params: ColorAdjustParams) -> Image.Image:
        """直接对Image对象应用调色"""
        if params.brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(params.brightness)
        if params.contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(params.contrast)
        if params.saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(params.saturation)
        if params.sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(params.sharpness)
        if params.temperature != 0:
            img = self._adjust_temperature(img, params.temperature)
        return img
    
    def list_styles(self) -> List[Dict[str, str]]:
        """列出所有可用风格"""
        return [
            {"id": s.value, "name": s.name, "description": self._get_style_description(s)}
            for s in ColorStyle
        ]
    
    def _get_style_description(self, style: ColorStyle) -> str:
        """获取风格描述"""
        descriptions = {
            ColorStyle.ORIGINAL: "原图，不做调整",
            ColorStyle.VIVID: "鲜艳，增强色彩和对比",
            ColorStyle.WARM: "暖色调，偏黄偏红",
            ColorStyle.COOL: "冷色调，偏蓝偏青",
            ColorStyle.VINTAGE: "复古，低饱和+暗角+颗粒",
            ColorStyle.CINEMATIC: "电影感，低亮高对比+暗角",
            ColorStyle.BW: "黑白，去色",
            ColorStyle.SEPIA: "怀旧棕褐色调",
            ColorStyle.HDR: "HDR效果，高动态范围",
            ColorStyle.SOFT: "柔和，低对比低锐度",
            ColorStyle.SHARP: "锐利，高对比高锐度",
            ColorStyle.DREAMY: "梦幻，高亮低对比柔焦",
            ColorStyle.CYBERPUNK: "赛博朋克，高饱和冷色调",
            ColorStyle.FILM: "胶片感，微暖+颗粒+暗角",
        }
        return descriptions.get(style, "")


# ============ 便捷函数 ============
def grade_image(image_path: str, style: str = "vivid", 
                output_path: str = None) -> str:
    """便捷函数：一键调色"""
    grader = SmartColorGrader()
    style_enum = ColorStyle(style) if style in [s.value for s in ColorStyle] else ColorStyle.VIVID
    return grader.apply_style(image_path, style_enum, output_path)


def auto_grade_image(image_path: str, output_path: str = None) -> str:
    """便捷函数：自动调色"""
    grader = SmartColorGrader()
    return grader.auto_grade(image_path, output_path=output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    grader = SmartColorGrader()
    
    print("=" * 60)
    print("智能调色工具")
    print("=" * 60)
    print(f"Pillow可用: {PILLOW_AVAILABLE}")
    print(f"\n可用风格 ({len(ColorStyle)}种):")
    for style in grader.list_styles():
        print(f"  - {style['name']} ({style['id']}): {style['description']}")
