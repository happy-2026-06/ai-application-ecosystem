FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

ARG BACKEND_HOST=backend
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://${BACKEND_HOST}:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;

        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

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
