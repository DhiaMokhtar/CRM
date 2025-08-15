# Multi-stage build for Angular frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including devDependencies) for building
RUN npm ci --silent

# Copy source code
COPY . .

# Build the Angular app for production
RUN npm run build:prod

# Production stage with Nginx and HTTPS
FROM nginx:alpine

# Install OpenSSL for certificate handling
RUN apk add --no-cache openssl curl

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl

# Copy built app from builder stage
COPY --from=builder /app/dist/frond-end/browser /usr/share/nginx/html

# Copy HTTPS nginx configuration
COPY nginx-https.conf /etc/nginx/conf.d/default.conf

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Health check for HTTPS
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -k -f https://localhost:443 || exit 1

# Expose HTTPS port
EXPOSE 80 443

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]