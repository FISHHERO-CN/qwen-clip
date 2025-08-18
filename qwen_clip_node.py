import os
import sys
import folder_paths
from .model_manager import ModelManager
from .utils import ImageCaptionGenerator

class QwenClipNode:
    def __init__(self):
        self.model_manager = ModelManager()
        self.caption_generator = None
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "model_type": (["qwen2.5-vl-7b-instruct", "custom"], {
                    "default": "qwen2.5-vl-7b-instruct"
                })    
            }
        }       
        

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("caption_chinese", "caption_english")
    FUNCTION = "generate_caption"
    CATEGORY = "QwenCLIP"

    def generate_caption(self, image, model_type, custom_model_path=""):
        try:
            # 初始化模型管理器
            if self.caption_generator is None:
                self.caption_generator = ImageCaptionGenerator()
            
            # 获取模型路径
            if model_type == "custom" and custom_model_path:
                model_path = custom_model_path
            else:
                model_path = self.model_manager.get_model_path(model_type)
                if not model_path:
                    model_path = self.model_manager.download_model(model_type)
            
            # 启动模型服务
            self.caption_generator.load_model(model_path, model_type)
            
            # 转换图像格式
            image_path = self.save_temp_image(image)
            
            # 生成中英文提示词
            chinese_caption, english_caption = self.caption_generator.generate_caption(
                image_path, detail_level
            )
            
            # 清理临时文件
            if os.path.exists(image_path):
                os.remove(image_path)
            
            # 停止模型服务
            self.caption_generator.unload_model()
            
            return (chinese_caption, english_caption)
            
        except Exception as e:
            # 确保模型服务被停止
            if self.caption_generator:
                self.caption_generator.unload_model()
            raise Exception(f"生成提示词失败: {str(e)}")

    def save_temp_image(self, image):
        """保存图像到临时文件"""
        import numpy as np
        from PIL import Image
        
        # 转换tensor到numpy
        image_np = image[0].cpu().numpy()
        
        # 转换到0-255范围
        image_np = (image_np * 255).astype(np.uint8)
        
        # 创建PIL图像
        pil_image = Image.fromarray(image_np)
        
        # 保存到临时文件
        temp_path = os.path.join(folder_paths.get_temp_directory(), "temp_image.png")
        pil_image.save(temp_path)
        
        return temp_path

# 节点映射
NODE_CLASS_MAPPINGS = {
    "QwenClipNode": QwenClipNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QwenClipNode": "图片提示词反推 (Qwen-CLIP)"
}
