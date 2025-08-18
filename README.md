# Qwen-CLIP ComfyUI Plugin

图片提示词反推插件，基于阿里Qwen模型。

## 功能特点

- 🤖 默认使用阿里Qwen模型
- 🌍 支持中英文双语输出
- 📝 支持简单和详细模式
- 🔄 自动下载和管理模型
- ⚡ 自动资源管理（启动/停止服务）

## 安装

1. 进入ComfyUI的`custom_nodes`目录
2. 克隆此仓库：
   ```bash
   git clone https://github.com/your-username/qwen-clip.git
安装依赖：
pip install -r requirements.txt
使用方法
在ComfyUI中找到"QwenCLIP"分类
添加"图片提示词反推"节点
连接图像输入
配置参数：
模型类型: 选择Qwen模型或自定义模型
输出语言: 中文或英文
详细程度: 简单或详细
自定义模型路径: 可选，用于指定本地模型路径
输出格式
简单模式
直接输出AI生成的简要描述

详细模式
按照以下结构输出：

主体（含权重）
位置关系
细节描述
风格特征
其他信息
模型管理
插件会自动在ComfyUI/models/clip目录下管理模型：

首次使用时自动下载所需模型
自动检测已存在的模型
支持自定义模型路径
注意事项
首次运行需要下载模型，可能需要较长时间
建议有足够的磁盘空间（模型通常几GB）
推荐使用GPU以获得更好的性能

## 使用说明

1. **安装**：
   - 将整个`qwen-clip`文件夹放入ComfyUI的`custom_nodes`目录
   - 在`qwen-clip`目录下运行`pip install -r requirements.txt`

2. **配置**：
   - 首次使用时会自动下载模型到`ComfyUI/models/clip`目录
   - 可以通过`custom_model_path`参数指定本地模型路径

3. **节点参数**：
   - `model_type`: 模型类型（qwen-vl, qwen-vl-chat, custom）
   - `output_language`: 输出语言（zh-CN, en-US）
   - `detail_level`: 详细程度（simple, detailed）
   - `custom_model_path`: 自定义模型路径（可选）

4. **输出**：
   - 返回两个字符串：中文提示词和英文提示词