import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from PIL import Image
import requests
from io import BytesIO

class ImageCaptionGenerator:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_type = None
        self.device = torch.device("cpu")
    
    def load_model(self, model_path, model_type):
        """加载模型"""
        try:
            if self.model is not None and self.model_type == model_type:
                return
            
            # 卸载现有模型
            self.unload_model()
            
            print(f"正在加载模型: {model_path}")
            
            # 加载分词器和模型
            try:
                # 尝试从本地路径加载模型
                self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
                # 创建一个临时目录用于模型卸载
                offload_folder = os.path.join(os.path.dirname(model_path), "offload")
                os.makedirs(offload_folder, exist_ok=True)
                
                try:
                    # 尝试使用auto设备映射
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_path, 
                        device_map="auto", 
                        offload_folder=offload_folder,  # 指定卸载文件夹
                        torch_dtype=torch.float16,  # 使用半精度浮点数减少内存使用
                        trust_remote_code=True
                    ).eval()
                    print(f"模型已加载，设备映射: auto")
                except Exception as e:
                    # 如果auto设备映射失败，尝试使用cpu
                    if "device string: disk" in str(e):
                        print(f"自动设备映射失败，尝试使用CPU: {str(e)}")
                        self.model = AutoModelForCausalLM.from_pretrained(
                            model_path, 
                            device_map="cpu", 
                            torch_dtype=torch.float16,  # 使用半精度浮点数减少内存使用
                            trust_remote_code=True
                        ).eval()
                        print(f"模型已加载，设备映射: cpu")
                    else:
                        raise e
                print(f"模型已加载，部分权重可能已卸载到: {offload_folder}")
            except Exception as e:
                # 如果本地加载失败，尝试从Hugging Face Hub下载
                print(f"本地模型加载失败: {str(e)}")
                print(f"尝试从Hugging Face Hub下载模型: {model_path}")
                try:
                    # 提取模型名称（假设model_path是完整路径）
                    model_name = os.path.basename(model_path)
                    self.tokenizer = AutoTokenizer.from_pretrained(f"qwen/{model_name}", trust_remote_code=True)
                    
                    # 创建一个临时目录用于模型卸载
                    offload_folder = os.path.join(os.path.dirname(model_path), "offload")
                    os.makedirs(offload_folder, exist_ok=True)
                    
                    try:
                        # 尝试使用auto设备映射
                        self.model = AutoModelForCausalLM.from_pretrained(
                            f"qwen/{model_name}", 
                            device_map="auto", 
                            offload_folder=offload_folder,  # 指定卸载文件夹
                            torch_dtype=torch.float16,  # 使用半精度浮点数减少内存使用
                            trust_remote_code=True
                        ).eval()
                        print(f"模型已从Hugging Face Hub加载，设备映射: auto")
                    except Exception as e:
                        # 如果auto设备映射失败，尝试使用cpu
                        if "device string: disk" in str(e):
                            print(f"自动设备映射失败，尝试使用CPU: {str(e)}")
                            self.model = AutoModelForCausalLM.from_pretrained(
                                f"qwen/{model_name}", 
                                device_map="cpu", 
                                torch_dtype=torch.float16,  # 使用半精度浮点数减少内存使用
                                trust_remote_code=True
                            ).eval()
                            print(f"模型已从Hugging Face Hub加载，设备映射: cpu")
                        else:
                            raise e
                    print(f"模型已从Hugging Face Hub加载，部分权重可能已卸载到: {offload_folder}")
                except Exception as e2:
                    raise Exception(f"从Hugging Face Hub下载模型失败: {str(e2)}")
            
            self.model_type = model_type
            print("模型加载完成")
            
        except Exception as e:
            raise Exception(f"模型加载失败: {str(e)}")
    
    def unload_model(self):
        """卸载模型"""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.model_type = None
        print("模型已卸载")
    
    def generate_caption(self, image_path, detail_level):
        """生成图像描述（中英文）"""
        if self.model is None or self.tokenizer is None:
            raise Exception("模型未加载")
        
        try:
            # 获取图像分辨率
            with Image.open(image_path) as img:
                width, height = img.size
            
            # 构建中文提示词，明确说明用于AI文生图
            prompt = f"请给我一段提示词，可以准确向其他文生图大模型描述这张图片，以生成相似的图片，返回文本需要包含中英文，给出json格式回答，具体内容是{'中文提示词':'','英文提示词':''}，描述内容尽可能详细，可能包括但不限于主体（含权重）、位置关系、细节、风格等"
            
            # 构建输入
            query = self.tokenizer.from_list_format([
                {'image': image_path},
                {'text': prompt},
            ])
            
            # 生成文本
            inputs = self.tokenizer(query, return_tensors='pt')
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                pred = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    top_k=50,
                    top_p=0.95,
                )
            
            response = self.tokenizer.decode(pred[0], skip_special_tokens=True)
            
            # 提取中文回答部分,解析json，格式{'中文提示词':'','英文提示词':''}，提取中英文提示词返回
            try:
                json_str = response.split("json")[1].strip()
                json_data = json.loads(json_str)
                chinese_caption = json_data['中文提示词']
                english_caption = json_data['英文提示词']
            except:
                chinese_caption = response
                english_caption = response  # 简单复制中文回答作为英文回答
                print(f"警告：无法解析JSON格式的回答，使用原始文本。原始回答: {response}")

            # 返回中英文版本
            return chinese_caption, english_caption
            
        except Exception as e:
            raise Exception(f"生成描述失败: {str(e)}")
    
    def __del__(self):
        """析构函数，确保模型被卸载"""
        self.unload_model()
