FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

# ── 生产阶段 ─────────────────────────────────────────
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# nginx 配置模板 —— 构建时注入 BACKEND_HOST
# 默认指向同项目的 backend 容器
ARG BACKEND_HOST=backend
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA 回退
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API 代理到后端
    location /api/ {
        proxy_pass http://${BACKEND_HOST}:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;

        # SSE 支持（流式响应）
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # API 文档
    location /api/docs {
        proxy_pass http://${BACKEND_HOST}:8000;
        proxy_set_header Host \$host;
    }
    location /api/redoc {
        proxy_pass http://${BACKEND_HOST}:8000;
        proxy_set_header Host \$host;
    }
}
EOF

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
