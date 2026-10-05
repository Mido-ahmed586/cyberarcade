FROM node:20-alpine

WORKDIR /app

# Install dependencies first (Docker cache layer)
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

EXPOSE 5173

# --host binds to 0.0.0.0 so the port is reachable from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
