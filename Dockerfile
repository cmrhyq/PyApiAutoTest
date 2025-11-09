# 使用官方Python运行时作为基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    openjdk-11-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# 安装Allure
RUN wget -O allure-2.24.0.tgz https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.24.0/allure-commandline-2.24.0.tgz \
    && tar -zxf allure-2.24.0.tgz -C /opt/ \
    && ln -s /opt/allure-2.24.0/bin/allure /usr/bin/allure \
    && rm allure-2.24.0.tgz

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/reports/allure-results \
    && mkdir -p /app/reports/allure-report \
    && mkdir -p /app/logs

# 设置权限
RUN chmod +x run_tests.py

# 暴露端口（用于Allure报告服务）
EXPOSE 8080

# 默认命令
CMD ["python", "run_tests.py", "--help"]