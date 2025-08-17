import os
import torch
import time
from threading import Thread
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import gradio as gr
import requests
from PIL import Image
import io

class QwenCLIPNode:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_thread = None
        self.model_running = False
        self.current_model_path = "Qwen/Qwen-VL-Chat"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "model_path": ("STRING", {"default": "Qwen/Qwen-VL-Chat", "multiline": False}),
                "mode": (["simple", "detailed"],),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("chinese_prompt", "english_prompt")
    FUNCTION = "generate_prompt"
    CATEGORY = "qwen-clip"

    # 节点图标 (base64 encoded SVG)
    ICON = "PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMzAgMEg1MHY2MEgzMFYweiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTAgMTBoNDB2MzBIMTBWMTR6IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIvPjxwYXRoIGQ9Ik0xNSAxNWgzMHYxNUgxNVYxNXoiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0iTTIwIDIwaDIwdjE1SDIwVjIwek0yNSAyNWgyMHY1SDI1VjI1ek0zMCAzMHY1SDM1VjMweiIgZmlsbD0iIzMzMyIvPjwvc3ZnPg=="

    def start_model_service(self, model_path):
        """启动模型服务"""
        try:
            self.model_running = True
            # 检查模型是否存在，不存在则下载
            if not os.path.exists(model_path):
                print(f"模型 {model_path} 不存在，开始下载...")
                # 实际下载会由transformers库自动处理

            # 加载模型和tokenizer
            print(f"加载模型: {model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            self.model.eval()
            self.current_model_path = model_path
            print("模型加载完成")
        except Exception as e:
            error_msg = f"模型加载失败: {str(e)}"
            print(error_msg)
            self.model_running = False
            # 记录错误信息供后续使用
            self.last_error = error_msg

    def stop_model_service(self):
        """停止模型服务并释放资源"""
        if self.model_running:
            self.model_running = False
            # 清除模型和tokenizer
            self.model = None
            self.tokenizer = None
            # 清理GPU内存
            torch.cuda.empty_cache()
            print("模型服务已停止，资源已释放")

    def generate_prompt(self, image, model_path, mode):
        """根据输入图像生成提示词"""
        try:
            # 如果模型路径改变或模型未运行，启动新的模型服务
            if model_path != self.current_model_path or not self.model_running:
                # 停止当前模型服务
                if self.model_running:
                    self.stop_model_service()
                    time.sleep(2)  # 等待资源释放

                # 启动新模型服务
                self.model_thread = Thread(target=self.start_model_service, args=(model_path,))
                self.model_thread.daemon = True
                self.model_thread.start()

                # 等待模型加载完成
                max_wait = 300  # 最多等待5分钟
                wait_time = 0
                while not self.model_running and wait_time < max_wait:
                    time.sleep(1)
                    wait_time += 1
                    if wait_time % 10 == 0:
                        print(f"等待模型加载中... ({wait_time}s)")

                if not self.model_running:
                    error_msg = f"模型加载超时: {self.last_error if hasattr(self, 'last_error') else '未知错误'}"
                    raise Exception(error_msg)

            # 准备图像
            # 将ComfyUI的IMAGE格式转换为PIL Image
            # 先将PyTorch张量转换为NumPy数组再使用astype
            img = Image.fromarray((image[0] * 255).cpu().numpy().astype('uint8'))

            # 构造提示，要求同时输出中英文
            if mode == "simple":
                prompt = "这是一张图片的描述，将用于AI大模型制作文生图或图生图。请先简洁明了地用中文描述这张图片，符合提示词习惯，然后用英文翻译同样的内容。请严格按照'中文：[内容]\n英文：[内容]'的格式输出。"
            else:
                prompt = "这是一张图片的描述，将用于AI大模型制作文生图或图生图。请先详细用中文描述这张图片，包括主体(含权重)+位置关系+细节+风格+其他要素，符合提示词习惯，然后用英文翻译同样的内容。请严格按照'中文：[内容]\n英文：[内容]'的格式输出。"

            # 生成提示词（一次调用）
            inputs = self.tokenizer.from_list_format([
                {"image": img},
                {"text": prompt},
            ])
            inputs = inputs.to(self.model.device)
            generated_ids = self.model.generate(**inputs, max_new_tokens=2048)
            full_response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            # 解析结果
            chinese_prompt = ""
            english_prompt = ""
            try:
                # 查找中文部分
                cn_start = full_response.find("中文：") + 3
                cn_end = full_response.find("\n英文：")
                if cn_start > 2 and cn_end > cn_start:
                    chinese_prompt = full_response[cn_start:cn_end].strip()

                # 查找英文部分
                en_start = full_response.find("英文：") + 3
                if en_start > 2:
                    english_prompt = full_response[en_start:].strip()

                # 如果解析失败，使用默认值
                if not chinese_prompt:
                    chinese_prompt = "解析中文提示词失败"
                if not english_prompt:
                    english_prompt = "Failed to parse English prompt"
            except Exception as e:
                chinese_prompt = f"解析错误: {str(e)}"
                english_prompt = f"Parsing error: {str(e)}"

            return chinese_prompt, english_prompt

        except Exception as e:
            error_msg = f"生成提示词失败: {str(e)}"
            print(error_msg)
            return f"错误: {error_msg}", f"Error: {error_msg}"
        finally:
            # 无论结果如何，停止模型服务
            self.stop_model_service()

# 注册节点
NODE_CLASS_MAPPINGS = {
    "QwenCLIPNode": QwenCLIPNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QwenCLIPNode": "Qwen CLIP Prompt Generator (Image to Text)"
}