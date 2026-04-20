FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# dist/ is copied out via docker cp in deploy.sh — no separate container needed
