FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y default-libmysqlclient-dev default-mysql-client build-essential pkg-config openssl && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/media /app/ssl

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .
RUN chmod 700 /app/ssl

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
EXPOSE 8000