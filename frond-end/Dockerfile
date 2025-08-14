# Multi-stage build for Angular frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with optimizations
RUN npm ci --only=production --silent

# Copy source code
COPY . .

# Build the Angular app
RUN npm run build -- --configuration production

# Production stage with Nginx
FROM nginx:alpine

# Copy built app from builder stage
COPY --from=builder /app/dist/frond-end/browser /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]