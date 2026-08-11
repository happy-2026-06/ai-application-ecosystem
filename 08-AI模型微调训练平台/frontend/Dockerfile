FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm config set registry https://registry.npmmirror.com && npm install --legacy-peer-deps
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
