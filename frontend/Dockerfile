# Stage 1: Build the React Application
FROM node:18-alpine AS build

WORKDIR /app

# Copy package config and install dependencies
COPY package*.json ./
RUN npm ci

# Copy codebase files
COPY . .

# Build step with production variables
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
