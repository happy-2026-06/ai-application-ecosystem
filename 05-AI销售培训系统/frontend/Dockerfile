FROM node:20-alpine

WORKDIR /app

# Reuse package.json from the build context, install deps
COPY package.json ./
RUN npm install --legacy-peer-deps

# Source code is mounted at runtime via docker-compose volumes

EXPOSE 5173

# Vite dev server (port 5173 = our standard)
# We always override with --port in docker-compose command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
