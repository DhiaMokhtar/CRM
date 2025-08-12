FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including MySQL client
RUN apt-get update && apt-get install -y default-libmysqlclient-dev default-mysql-client build-essential pkg-config openssl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .
# Ensure only a directory exists for SSL mount points; not file-named dirs
RUN rm -rf /app/ssl/localhost.pem /app/ssl/localhost-key.pem && mkdir -p /app/ssl /app/media && chmod 700 /app/ssl

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Expose port
EXPOSE 8000