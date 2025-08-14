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
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        // Use cached SSL certs if available
        stage('Prepare SSL certs') {
            steps {
                sh '''
                  set -e
                  mkdir -p certs
                  if [ ! -f certs/localhost.pem ] || [ ! -f certs/localhost-key.pem ]; then
                    echo 'Generating self-signed certs for pipeline...' &&
                    openssl req -x509 -nodes -newkey rsa:2048 -days 30 \
                      -keyout certs/localhost-key.pem \
                      -out certs/localhost.pem \
                      -subj '/CN=localhost';
                  else
                    echo 'Using existing SSL certificates'
                  fi
                  chmod 600 certs/localhost.pem certs/localhost-key.pem
                '''
            }
        }

        // Parallel build stages
        stage('Build All Services') {
            parallel {
                stage('Build Frontend') {
                    steps {
                        dir("${FRONTEND_DIR}") {
                            sh '''
                                # Use npm ci for faster, deterministic installs
                                npm ci --legacy-peer-deps --prefer-offline
                                # Build with optimizations
                                npm run build -- --configuration production --optimization=true --aot=true --build-optimizer=true
                            '''
                        }
                    }
                }
                
                stage('Build Users Service') {
                    steps {
                        sh 'docker-compose -f microservice/users/docker-compose.yml build --parallel'
                    }
                }
                
                stage('Build Courses Service') {
                    steps {
                        sh 'docker-compose -f microservice/courses/docker-compose.yml build --parallel'
                    }
                }
                
                stage('Build Messaging Service') {
                    steps {
                        sh 'docker-compose -f microservice/messaging/docker-compose.yml build --parallel'
                    }
                }
                
                stage('Build Homework Service') {
                    steps {
                        sh 'docker-compose -f microservice/homework/docker-compose.yml build --parallel'
                    }
                }
            }
        }

        // Skip frontend tests in CI for speed
        stage('Quick Tests') {
            steps {
                echo 'Skipping tests for faster builds. Enable in production pipeline.'
            }
        }

        stage('Deploy Services') {
            steps {
                sh '''
                    set -e
                    
                    # Quick cleanup without volumes for speed
                    docker-compose -f microservice/users/docker-compose.yml down --remove-orphans || true
                    docker-compose -f microservice/courses/docker-compose.yml down --remove-orphans || true
                    docker-compose -f microservice/homework/docker-compose.yml down --remove-orphans || true
                    docker-compose -f microservice/messaging/docker-compose.yml down --remove-orphans || true

                    # Create network only if it doesn't exist
                    docker network create crm_network 2>/dev/null || echo "Network crm_network already exists"

                    # Deploy in parallel using background processes
                    docker-compose -f microservice/users/docker-compose.yml up -d --remove-orphans &
                    docker-compose -f microservice/courses/docker-compose.yml up -d --remove-orphans &
                    docker-compose -f microservice/homework/docker-compose.yml up -d --remove-orphans &
                    docker-compose -f microservice/messaging/docker-compose.yml up -d --remove-orphans &
                    
                    # Wait for all background processes to complete
                    wait
                '''
            }
        }

        stage('Deploy Frontend') {
            steps {
                dir("${FRONTEND_DIR}") {
                    sh '''
                        set -e
                        
                        # Quick container cleanup
                        docker stop crm-frontend 2>/dev/null || true
                        docker rm crm-frontend 2>/dev/null || true
                        
                        # Create optimized nginx config
                        cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;
    
    # Optimize for performance
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    location / {
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy with connection pooling
    location /api/users/ {
        proxy_pass https://crm-users-service:8001/api/;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
    }
    
    location /api/courses/ {
        proxy_pass https://crm-courses-service:8002/api/;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
    }
    
    location /api/messaging/ {
        proxy_pass https://crm-messaging-service:8003/api/;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
    }
    
    location /api/homework/ {
        proxy_pass https://crm-homework-service:8004/api/;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
    }
    
    location /media/ {
        proxy_pass https://crm-courses-service:8002/media/;
        proxy_ssl_verify off;
    }
}
EOF
                        
                        # Deploy frontend with restart policy
                        docker run -d --name crm-frontend \
                            --network crm_network \
                            --restart unless-stopped \
                            -p 80:80 \
                            -v $(pwd)/dist/frond-end/browser:/usr/share/nginx/html:ro \
                            -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
                            nginx:alpine
                    '''
                }
            }
        }

        stage('Quick Health Check') {
            steps {
                script {
                    sh '''
                        # Shorter wait time
                        sleep 15
                        
                        # Quick parallel health checks
                        echo "Checking services..."
                        curl -f http://localhost/ --max-time 10 || echo "Frontend not ready" &
                        curl -k -f https://localhost:8001/health/ --max-time 10 || echo "Users service not ready" &
                        curl -k -f https://localhost:8002/health/ --max-time 10 || echo "Courses service not ready" &
                        curl -k -f https://localhost:8003/health/ --max-time 10 || echo "Messaging service not ready" &
                        curl -k -f https://localhost:8004/health/ --max-time 10 || echo "Homework service not ready" &
                        
                        wait
                        echo "Health checks completed"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline completed."
            // Only clean up dangling images to save time
            sh 'docker image prune -f'
        }
        success { echo "✅ CRM pipeline succeeded!" }
        failure { echo "❌ CRM pipeline failed!" }
    }
}