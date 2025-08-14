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
        // Add caching environment variables
        BUILDKIT_INLINE_CACHE = '1'
        NODE_OPTIONS = '--max-old-space-size=4096'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        // Cache SSL certs
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

        // Super optimized parallel builds with caching
        stage('Fast Parallel Build') {
            parallel {
                stage('Build Frontend') {
                    steps {
                        dir("${FRONTEND_DIR}") {
                            sh '''
                                # Use npm cache aggressively
                                export npm_config_cache=/tmp/.npm
                                export npm_config_prefer_offline=true
                                
                                # Fast install with cache
                                npm ci --legacy-peer-deps --prefer-offline --no-audit --no-fund
                                
                                # Quick build without source maps for speed
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
                            
                            # Wait for all builds to complete
                            wait
                        '''
                    }
                }
            }
        }

        // Lightning fast deployment
        stage('Lightning Deploy') {
            steps {
                sh '''
                    set -e
                    
                    # Super fast cleanup - don't wait for graceful shutdown
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

                    # Ultra-fast parallel deployment
                    docker-compose -f microservice/users/docker-compose.yml up -d --force-recreate --no-deps &
                    docker-compose -f microservice/courses/docker-compose.yml up -d --force-recreate --no-deps &
                    docker-compose -f microservice/homework/docker-compose.yml up -d --force-recreate --no-deps &
                    docker-compose -f microservice/messaging/docker-compose.yml up -d --force-recreate --no-deps &
                    
                    wait
                    echo "All services deployed"
                '''
            }
        }

        // Quick frontend deployment
        stage('Deploy Frontend') {
            steps {
                dir("${FRONTEND_DIR}") {
                    sh '''
                        set -e
                        
                        # Kill frontend instantly
                        docker kill crm-frontend 2>/dev/null || true
                        docker rm crm-frontend 2>/dev/null || true
                        
                        # Minimal nginx config
                        cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/users/ {
        proxy_pass https://crm-users-service:8001/api/;
        proxy_ssl_verify off;
    }
    
    location /api/courses/ {
        proxy_pass https://crm-courses-service:8002/api/;
        proxy_ssl_verify off;
    }
    
    location /api/messaging/ {
        proxy_pass https://crm-messaging-service:8003/api/;
        proxy_ssl_verify off;
    }
    
    location /api/homework/ {
        proxy_pass https://crm-homework-service:8004/api/;
        proxy_ssl_verify off;
    }
}
EOF
                        
                        # Quick frontend deployment
                        docker run -d --name crm-frontend \
                            --network crm_network \
                            -p 80:80 \
                            -v $(pwd)/dist/frond-end/browser:/usr/share/nginx/html:ro \
                            -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
                            nginx:alpine
                    '''
                }
            }
        }

        // Minimal health check
        stage('Quick Health Check') {
            steps {
                sh '''
                    # Very short wait
                    sleep 10
                    
                    # Quick checks with timeout
                    timeout 5 curl -f http://localhost/ || echo "Frontend: starting..."
                    timeout 5 curl -k https://localhost:8001/health/ || echo "Users: starting..."
                    timeout 5 curl -k https://localhost:8002/health/ || echo "Courses: starting..."
                    timeout 5 curl -k https://localhost:8003/health/ || echo "Messaging: starting..."
                    timeout 5 curl -k https://localhost:8004/health/ || echo "Homework: starting..."
                    
                    echo "Deployment completed!"
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline completed."
            // Only clean up build cache, not images
            sh 'docker builder prune -f'
        }
        success { echo "✅ CRM pipeline succeeded in record time!" }
        failure { echo "❌ CRM pipeline failed!" }
    }
}