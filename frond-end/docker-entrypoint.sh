#!/bin/sh
set -e

echo "🔒 Setting up HTTPS for frontend..."

# Create SSL directory if it doesn't exist
mkdir -p /etc/nginx/ssl

# Check if SSL certificates exist, if not generate self-signed ones
if [ ! -f /etc/nginx/ssl/localhost.pem ] || [ ! -f /etc/nginx/ssl/localhost-key.pem ]; then
    echo "🔑 Generating self-signed SSL certificates..."
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
        -keyout /etc/nginx/ssl/localhost-key.pem \
        -out /etc/nginx/ssl/localhost.pem \
        -subj "/CN=localhost/O=CRM Frontend/C=US"
    
    # Set proper permissions
    chmod 600 /etc/nginx/ssl/localhost-key.pem
    chmod 644 /etc/nginx/ssl/localhost.pem
else
    echo "✅ SSL certificates found"
fi

# List SSL files for debugging
echo "📋 SSL certificate files:"
ls -la /etc/nginx/ssl/

# Test nginx configuration
echo "🔧 Testing Nginx configuration..."
nginx -t

echo "🚀 Starting Nginx with HTTPS..."
exec "$@"