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
 echo "All services deployed"
        stage('Deploy Frontend') {   '''
            steps {   }
                dir("${FRONTEND_DIR}") {        }
                    sh '''
                        set -ent
                        oy Frontend') {
                        # Create nginx config with correct port
                        cat > nginx.conf << 'EOF'NTEND_DIR}") {
server {
    listen 80;set -e
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;ue
    docker rm crm-frontend 2>/dev/null || true
    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;                cat > nginx.conf << 'EOF'
    
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";ginx/html;
    }index index.html;
    
    location /api/users/ {
        proxy_pass https://crm-users-service:8001/api/;   try_files $uri $uri/ /index.html;
        proxy_ssl_verify off;}
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;m-users-service:8001/api/;
        proxy_set_header X-Forwarded-Proto $scheme;   proxy_ssl_verify off;
    }}
    
    location /api/courses/ {
        proxy_pass https://crm-courses-service:8002/api/;m-courses-service:8002/api/;
        proxy_ssl_verify off;   proxy_ssl_verify off;
        proxy_set_header Host $host;}
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;m-messaging-service:8003/api/;
    }   proxy_ssl_verify off;
    }
    location /api/messaging/ {
        proxy_pass https://crm-messaging-service:8003/api/;
        proxy_ssl_verify off;m-homework-service:8004/api/;
        proxy_set_header Host $host;   proxy_ssl_verify off;
        proxy_set_header X-Real-IP $remote_addr;   }
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/homework/ {ontend \
        proxy_pass https://crm-homework-service:8004/api/;crm_network \
        proxy_ssl_verify off;
        proxy_set_header Host $host;o \
        proxy_set_header X-Real-IP $remote_addr;inx.conf:/etc/nginx/conf.d/default.conf:ro \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;     nginx:alpine
        proxy_set_header X-Forwarded-Proto $scheme;   '''
    }   }
}   }
EOF        }
                        
                        # Check if port is available, if not find an alternative
                        if netstat -tuln | grep -q ":${FRONTEND_PORT} "; thenk Health Check') {
                            echo "Port ${FRONTEND_PORT} is in use, trying port 8090"
                            FRONTEND_PORT=8090
                        fihort wait
                        sleep 10
                        if netstat -tuln | grep -q ":${FRONTEND_PORT} "; then
                            echo "Port ${FRONTEND_PORT} is in use, trying port 9090"
                            FRONTEND_PORT=9090
                        fi
                        
                        echo "Using port ${FRONTEND_PORT} for frontend""
                        timeout 5 curl -k https://localhost:8004/health/ || echo "Homework: starting..."
                        # Deploy frontend with available port
                        docker run -d --name crm-frontend \ echo "Deployment completed!"
                            --network crm_network \   '''
                            -p ${FRONTEND_PORT}:80 \   }
                            -v $(pwd)/dist/frond-end/browser:/usr/share/nginx/html:ro \   }
                            -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \    }
                            nginx:alpine
                            
                        echo "Frontend deployed on port ${FRONTEND_PORT}"
                    '''
                }, not images
            }   sh 'docker builder prune -f'
        }
in record time!" }
        stage('Health Check') {   failure { echo "❌ CRM pipeline failed!" }
            steps {   }






































































}    }        }            '''                docker network ls                echo "Network status:"                netstat -tuln | grep ":80\\|:8080\\|:8090\\|:9090" || echo "No conflicting ports found"                echo "Port usage:"                docker ps -a                echo "Running containers:"                echo "=== Debug Information ==="            sh '''            echo "❌ CRM pipeline failed!"        failure {         }            '''                echo "✅ CRM pipeline succeeded! Frontend available at http://localhost:${FRONTEND_PORT}"                fi                    fi                        FRONTEND_PORT=9090                    elif docker port crm-frontend | grep -q "80/tcp -> 0.0.0.0:9090"; then                        FRONTEND_PORT=8090                    if docker port crm-frontend | grep -q "80/tcp -> 0.0.0.0:8090"; then                if ! docker port crm-frontend | grep -q "80/tcp -> 0.0.0.0:8080"; then                FRONTEND_PORT=8080                # Determine which port was used            sh '''        success {         }            sh 'docker builder prune -f'            echo "Pipeline completed."        always {    post {    }        }            }                '''                    echo "📝 Homework API: https://localhost:8004"                    echo "💬 Messaging API: https://localhost:8003"                    echo "📚 Courses API: https://localhost:8002"                    echo "🔐 Users API: https://localhost:8001"                    echo "🌐 Frontend available at: http://localhost:${FRONTEND_PORT}"                    echo "✅ Deployment completed successfully!"                                        timeout 10 curl -k https://localhost:8004/health/ || echo "Homework: still starting..."                    timeout 10 curl -k https://localhost:8003/health/ || echo "Messaging: still starting..."                    timeout 10 curl -k https://localhost:8002/health/ || echo "Courses: still starting..."                    timeout 10 curl -k https://localhost:8001/health/ || echo "Users: still starting..."                    timeout 10 curl -f http://localhost:${FRONTEND_PORT}/ || echo "Frontend: still starting..."                    # Health checks with proper timeouts                                        echo "Checking health on port ${FRONTEND_PORT}..."                                        fi                        fi                            FRONTEND_PORT=9090                        elif netstat -tuln | grep ":9090 " | grep -q LISTEN; then                            FRONTEND_PORT=8090                        if netstat -tuln | grep ":8090 " | grep -q LISTEN; then                    if ! netstat -tuln | grep ":8080 " | grep -q LISTEN; then                    FRONTEND_PORT=8080                    # Determine which port was used for frontend                                        sleep 15                    echo "Waiting for services to start..."                    # Wait for services to start                                        set -e                sh '''}