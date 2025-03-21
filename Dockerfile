FROM python:3.9-slim

WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建上传文件夹
RUN mkdir -p uploads

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=1832

# 暴露端口
EXPOSE 1832

# 启动应用
CMD ["python", "app.py"] 