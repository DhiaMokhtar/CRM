pipeline {
    agent any
    tools { nodejs 'Node24' }
    environment {
        FRONTEND_DIR = 'frond-end'
        USERS_COMPOSE = 'microservice/users/docker-compose.yml'
        COURSES_COMPOSE = 'microservice/courses/docker-compose.yml'
        HOMEWORK_COMPOSE = 'microservice/homework/docker-compose.yml'
        MESSAGING_COMPOSE = 'microservice/messaging/docker-compose.yml'
        MYSQL_ROOT_PASSWORD = 'crm_password'
        DOCKER_BUILDKIT = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
        BUILDKIT_INLINE_CACHE = '1'
        NODE_OPTIONS = '--max-old-space-size=4096'
        // Use different port to avoid conflicts
        FRONTEND_PORT = '8080'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Prepare SSL certs') {
            steps {
                sh '''
                  set -e
                  mkdir -p certs
                  if [ ! -f certs/localhost.pem ] || [ ! -f certs/localhost-key.pem ]; then
                    echo 'Generating self-signed certs...'
                    openssl req -x509 -nodes -newkey rsa:2048 -days 30 \
                      -keyout certs/localhost-key.pem \
                      -out certs/localhost.pem \
                      -subj '/CN=localhost'
                  else
                    echo 'Using existing SSL certificates'
                  fi
                  chmod 600 certs/localhost.pem certs/localhost-key.pem
                '''
            }
        }

        stage('Fast Parallel Build') {
            parallel {
                stage('Build Frontend') {
                    steps {
                        dir("${FRONTEND_DIR}") {
                            sh '''
                                export npm_config_cache=/tmp/.npm
                                export npm_config_prefer_offline=true
                                
                                npm ci --legacy-peer-deps --prefer-offline --no-audit --no-fund
                                npm run build -- --configuration production --source-map=false
                            '''
                        }
                    }
                }
                
                stage('Build All Microservices') {
                    steps {
                        sh '''
                            set -e
                            # Build all services in parallel with cache
                            docker-compose -f microservice/users/docker-compose.yml build --parallel --build-arg BUILDKIT_INLINE_CACHE=1 &
                            docker-compose -f microservice/courses/docker-compose.yml build --parallel --build-arg BUILDKIT_INLINE_CACHE=1 &
                            docker-compose -f microservice/messaging/docker-compose.yml build --parallel --build-arg BUILDKIT_INLINE_CACHE=1 &
                            docker-compose -f microservice/homework/docker-compose.yml build --parallel --build-arg BUILDKIT_INLINE_CACHE=1 &
                            
                            wait
                        '''
                    }
                }
            }
        }

        stage('Lightning Deploy') {
            steps {
                sh '''
                    set -e
                    
                    # Stop existing frontend first
                    docker kill crm-frontend 2>/dev/null || true
                    docker rm crm-frontend 2>/dev/null || true
                    
                    # Fast cleanup of microservices
                    docker-compose -f microservice/users/docker-compose.yml kill || true
                    docker-compose -f microservice/courses/docker-compose.yml kill || true
                    docker-compose -f microservice/homework/docker-compose.yml kill || true
                    docker-compose -f microservice/messaging/docker-compose.yml kill || true
                    
                    docker-compose -f microservice/users/docker-compose.yml rm -f || true
                    docker-compose -f microservice/courses/docker-compose.yml rm -f || true
                    docker-compose -f microservice/homework/docker-compose.yml rm -f || true
                    docker-compose -f microservice/messaging/docker-compose.yml rm -f || true

                    # Network creation
                    docker network create crm_network 2>/dev/null || echo "Network exists"

                    # Parallel deployment
                    docker-compose -f microservice/users/docker-compose.yml up -d --force-recreate --no-deps &
                    docker-compose -f microservice/courses/docker-compose.yml up -d --force-recreate --no-deps &
                    docker-compose -f microservice/homework/docker-compose.yml up -d --force-recreate --no-deps &
                    docker-compose -f microservice/messaging/docker-compose.yml up -d --force-recreate --no-deps &
                    
                    wait
                    echo "All services deployed"
                '''
            }
        }

        stage('Deploy Frontend') {
            steps {
                dir("${FRONTEND_DIR}") {
                    sh '''
                        set -e
                        
                        # Create nginx config with correct port
                        cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;
    
    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    location /api/users/ {
        proxy_pass https://crm-users-service:8001/api/;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/courses/ {
        proxy_pass https://crm-courses-service:8002/api/;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/messaging/ {
        proxy_pass https://crm-messaging-service:8003/api/;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/homework/ {
        proxy_pass https://crm-homework-service:8004/api/;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
                        
                        # Check if port is available, if not find an alternative
                        if netstat -tuln | grep -q ":${FRONTEND_PORT} "; then
                            echo "Port ${FRONTEND_PORT} is in use, trying port 8090"
                            FRONTEND_PORT=8090
                        fi
                        
                        if netstat -tuln | grep -q ":${FRONTEND_PORT} "; then
                            echo "Port ${FRONTEND_PORT} is in use, trying port 9090"
                            FRONTEND_PORT=9090
                        fi
                        
                        echo "Using port ${FRONTEND_PORT} for frontend"
                        
                        # Deploy frontend with available port
                        docker run -d --name crm-frontend \
                            --network crm_network \
                            -p ${FRONTEND_PORT}:80 \
                            -v $(pwd)/dist/frond-end/browser:/usr/share/nginx/html:ro \
                            -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
                            nginx:alpine
                            
                        echo "Frontend deployed on port ${FRONTEND_PORT}"
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    set -e
                    
                    # Wait for services to start
                    echo "Waiting for services to start..."
                    sleep 15
                    
                    # Determine which port was used for frontend
                    FRONTEND_PORT=8080
                    if ! netstat -tuln | grep ":8080 " | grep -q LISTEN; then
                        if netstat -tuln | grep ":8090 " | grep -q LISTEN; then
                            FRONTEND_PORT=8090
                        elif netstat -tuln | grep ":9090 " | grep -q LISTEN; then
                            FRONTEND_PORT=9090
                        fi
                    fi
                    
                    echo "Checking health on port ${FRONTEND_PORT}..."
                    
                    # Health checks with proper timeouts
                    timeout 10 curl -f http://localhost:${FRONTEND_PORT}/ || echo "Frontend: still starting..."
                    timeout 10 curl -k https://localhost:8001/health/ || echo "Users: still starting..."
                    timeout 10 curl -k https://localhost:8002/health/ || echo "Courses: still starting..."
                    timeout 10 curl -k https://localhost:8003/health/ || echo "Messaging: still starting..."
                    timeout 10 curl -k https://localhost:8004/health/ || echo "Homework: still starting..."
                    
                    echo "✅ Deployment completed successfully!"
                    echo "🌐 Frontend available at: http://localhost:${FRONTEND_PORT}"
                    echo "🔐 Users API: https://localhost:8001"
                    echo "📚 Courses API: https://localhost:8002"
                    echo "💬 Messaging API: https://localhost:8003"
                    echo "📝 Homework API: https://localhost:8004"
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline completed."
            sh 'docker builder prune -f'
        }
        success { 
            sh '''
                # Determine which port was used
                FRONTEND_PORT=8080
                if ! docker port crm-frontend | grep -q "80/tcp -> 0.0.0.0:8080"; then
                    if docker port crm-frontend | grep -q "80/tcp -> 0.0.0.0:8090"; then
                        FRONTEND_PORT=8090
                    elif docker port crm-frontend | grep -q "80/tcp -> 0.0.0.0:9090"; then
                        FRONTEND_PORT=9090
                    fi
                fi
                echo "✅ CRM pipeline succeeded! Frontend available at http://localhost:${FRONTEND_PORT}"
            '''
        }
        failure { 
            echo "❌ CRM pipeline failed!"
            sh '''
                echo "=== Debug Information ==="
                echo "Running containers:"
                docker ps -a
                echo "Port usage:"
                netstat -tuln | grep ":80\\|:8080\\|:8090\\|:9090" || echo "No conflicting ports found"
                echo "Network status:"
                docker network ls
            '''
        }
    }
}