FROM node:20-alpine

WORKDIR /app

COPY package.json ./
# Use npm mirror for faster installs in China
RUN npm config set registry https://registry.npmmirror.com && npm install --legacy-peer-deps

# Source code is mounted at runtime via docker-compose volumes
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
