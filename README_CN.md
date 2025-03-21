# DataSheet AI Analyzer

基于Flask的智能表格分析工具，使用AI技术分析Excel和CSV文件，支持自然语言查询和数据分析。

[English](README.md) | 简体中文

## 特性

- 🤖 AI驱动的数据分析
- 📊 支持Excel (.xlsx, .xls) 和 CSV文件
- 💬 自然语言查询界面
- 📈 数据可视化
- 🔄 自动重试机制
- 🌐 多API支持 (OpenAI等)

## 系统要求

- Python 3.7+
- pip（Python包管理器）
- 现代浏览器（Chrome, Firefox, Safari等）

## 安装步骤

1. 克隆项目到本地：
```bash
git clone [你的仓库地址]
cd datasheet-ai-analyzer
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动应用：
```bash
python app.py
```

应用将在 http://localhost:1832 运行

## 使用说明

### 1. API配置

首次使用需要配置API信息：
- API类型：选择使用的API服务（如OpenAI）
- API密钥：输入您的API密钥
- API地址：（可选）如果使用自定义API地址
- 最大重试次数：设置分析失败时的重试次数

### 2. 文件上传

- 支持的文件格式：Excel (.xlsx, .xls) 和 CSV (.csv)
- 点击"上传文件"按钮或将文件拖拽到指定区域
- 上传后可以预览文件内容（默认显示前10行，可展开查看更多）

### 3. 数据分析

1. 上传文件后，系统会自动分析文件的基本信息：
   - 列数和行数
   - 数据类型
   - 基本统计信息

2. 在查询框中输入自然语言问题，例如：
   - "统计每个类别的数量"
   - "计算销售总额"
   - "生成数据可视化图表"

3. 选择合适的模型（如果API支持多个模型）

4. 点击"分析"按钮开始分析

### 4. 查看结果

- 分析结果会以结构化形式展示
- 支持文本说明和数据可视化
- 如果分析失败，可以使用重试功能

## 配置说明

主要配置在config.py中，包括：
- UPLOAD_FOLDER：文件上传目录
- API相关配置（API_KEY, API_BASE等）
- 最大重试次数（MAX_RETRIES）

## 注意事项

1. 上传的文件会被临时保存在uploads目录中
2. 确保API配置正确，否则可能导致分析失败
3. 较大的文件可能需要更长的处理时间
