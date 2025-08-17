# Qwen-CLIP for ComfyUI

这是一个ComfyUI节点插件，用于从图像生成提示词(prompt)。该插件默认使用阿里的Qwen模型，并支持切换到其他模型。

## 功能特点

- 图片提示词反推：从输入图像生成描述性提示词
- 多模型支持：默认使用Qwen-VL-Chat，可自定义模型路径
- 双语输出：同时生成中文和英文提示词
- 两种模式：简单模式和详细模式
  - 简单模式：简洁明了的描述
  - 详细模式：包含主体(含权重)+位置关系+细节+风格+其他要素的详细描述
- 资源管理：自动启动和停止模型服务，优化资源使用

## 安装方法

1. 将本文件夹`qwen-clip`复制到ComfyUI的`custom_nodes`目录下
2. 安装依赖：
   ```bash
   cd custom_nodes/qwen-clip
   pip install -r requirements.txt
   ```
3. 重启ComfyUI

## 使用方法

1. 在ComfyUI中，从节点面板的`qwen-clip`类别中拖出`Qwen CLIP Prompt Generator`节点
2. 连接图像输入
3. 可选：修改模型路径、选择输出模式
4. 运行工作流，获取中英文提示词输出

## 注意事项

- 首次使用时，会自动下载模型，可能需要一些时间，请耐心等待
- 模型运行需要一定的GPU内存，建议使用具有至少8GB VRAM的显卡
- 详细模式生成的提示词会更丰富，但可能需要更长的处理时间

## 示例

简单模式输出示例：
- 中文："一只猫坐在沙发上，背景是客厅"
- 英文："A cat sitting on a sofa in a living room"

详细模式输出示例：
- 中文："[主体:猫(1.0)]坐在[位置:沙发(0.8)]上，[细节:猫的毛色为黑白相间，眼睛是蓝色的，尾巴卷曲着]，[风格:现实主义照片]，[其他:背景中可以看到模糊的电视和书架]"
- 英文："[Subject: cat(1.0)] sitting on [Position: sofa(0.8)], [Details: the cat has black and white fur, blue eyes, and a curled tail], [Style: realistic photograph], [Other: a blurred TV and bookshelf can be seen in the background]"