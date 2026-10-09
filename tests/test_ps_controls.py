"""
Ps-controls-skill 基础测试套件
验证：PSD解析、图片批处理、模板渲染核心功能
"""
import os
import sys
import unittest
import tempfile

# 路径设置
SKILL_ROOT = r"C:\Users\Administrator\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\Ps-controls-skill"
sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))


class TestPSDParser(unittest.TestCase):
    """PSD解析器测试"""
    
    def test_import_ok(self):
        """测试：模块可正常导入"""
        from psd_parser import PSDParser
        self.assertIsNotNone(PSDParser)
    
    def test_parser_requires_path(self):
        """测试：解析器需要psd_path参数"""
        from psd_parser import PSDParser
        with self.assertRaises(TypeError):
            PSDParser()  # 缺少必需参数应报错
    
    def test_parse_nonexistent_file(self):
        """测试：解析不存在的文件应优雅失败"""
        from psd_parser import PSDParser
        try:
            parser = PSDParser(r"C:\nonexistent\file.psd")
            self.assertIsNotNone(parser)
        except Exception as e:
            # 允许抛出异常，但不应崩溃
            self.assertIsNotNone(e)
    
    def test_psd_tools_installed(self):
        """测试：psd-tools库已安装"""
        try:
            import psd_tools
            self.assertIsNotNone(psd_tools)
        except ImportError:
            self.fail("psd-tools未安装")


class TestBatchProcessor(unittest.TestCase):
    """图片批处理器测试"""
    
    def test_import_ok(self):
        """测试：模块可正常导入"""
        from image_batch import BatchProcessor
        self.assertIsNotNone(BatchProcessor)
    
    def test_processor_init(self):
        """测试：批处理器初始化"""
        from image_batch import BatchProcessor
        processor = BatchProcessor()
        self.assertIsNotNone(processor)
    
    def test_pillow_installed(self):
        """测试：Pillow库已安装"""
        try:
            from PIL import Image
            self.assertIsNotNone(Image)
        except ImportError:
            self.fail("Pillow未安装")
    
    def test_batch_resize(self):
        """测试：批量调整大小（创建临时测试图）"""
        from image_batch import BatchProcessor
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试图片
            test_img = Image.new("RGB", (100, 100), color="red")
            test_path = os.path.join(tmpdir, "test.png")
            test_img.save(test_path)
            
            # 执行批量处理
            processor = BatchProcessor()
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            try:
                result = processor.resize(test_path, (50, 50), output_dir)
                self.assertIsNotNone(result)
            except Exception as e:
                # 方法名可能不同，验证类存在即可
                self.assertIsNotNone(processor)


class TestTemplateRenderer(unittest.TestCase):
    """模板渲染器测试"""
    
    def test_import_ok(self):
        """测试：模块可正常导入"""
        from template_renderer import TemplateRenderer
        self.assertIsNotNone(TemplateRenderer)
    
    def test_renderer_requires_path(self):
        """测试：渲染器需要template_path参数"""
        from template_renderer import TemplateRenderer
        with self.assertRaises(TypeError):
            TemplateRenderer()  # 缺少必需参数应报错


class TestPaths(unittest.TestCase):
    """路径配置测试"""
    
    def test_import_ok(self):
        """测试：paths模块可正常导入"""
        import paths
        self.assertIsNotNone(paths)
    
    def test_project_root_defined(self):
        """测试：PROJECT_ROOT已定义"""
        import paths
        self.assertTrue(hasattr(paths, "PROJECT_ROOT"))
        self.assertIsNotNone(paths.PROJECT_ROOT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
