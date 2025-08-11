FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    default-mysql-client \
    build-essential \
    pkg-config \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Create media and ssl directories
RUN mkdir -p /app/media /app/ssl

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .
RUN rm -rf /app/ssl/localhost.pem /app/ssl/localhost-key.pem && mkdir -p /app/ssl /app/fileCourses /app/media && chmod 700 /app/ssl

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]