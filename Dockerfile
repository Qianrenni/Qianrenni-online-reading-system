# 使用官方 Python 基础镜像
FROM python:3.9-slim
# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app
# 设置环境变量，指定 Flask 环境
ENV FLASK_APP=run.py
# 使用清华大学的 PyPI 镜像源安装依赖
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 安装 Gunicorn
RUN pip install --no-cache-dir gunicorn

# 暴露端口
EXPOSE 5000

# 直接使用 Gunicorn 启动应用
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "run:app"]