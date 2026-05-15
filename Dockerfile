# ===== Stage 1: Build Frontend =====
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ===== Stage 2: Production Image =====
FROM python:3.12-slim

# 安装 Nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip install --no-cache-dir gunicorn

# 复制后端代码
COPY backend/ /app/backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# 创建数据目录
RUN mkdir -p /app/data /app/media /app/backend/staticfiles

# 复制 Nginx 配置和启动脚本
COPY docker/nginx.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default \
    && echo "daemon off;" >> /etc/nginx/nginx.conf

COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 环境变量
ENV DJANGO_SETTINGS_MODULE=musk.settings
ENV DB_DIR=/app/data
ENV MEDIA_ROOT=/app/media
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1

EXPOSE 80

# 数据卷
VOLUME ["/app/data", "/app/media"]

ENTRYPOINT ["/app/entrypoint.sh"]
