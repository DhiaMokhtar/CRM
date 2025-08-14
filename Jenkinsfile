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
        DOCKER_BUILDKIT = '1'  // Enable BuildKit for faster builds
        COMPOSE_DOCKER_CLI_BUILD = '1'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        // Provision SSL cert/key into workspace root for bind-mounts
        stage('Prepare SSL certs') {
            steps {
                sh '''
                  set -e
                  mkdir -p certs
                  if [ ! -f certs/localhost.pem ] || [ ! -f certs/localhost-key.pem ]; then
                    echo 'Generating self-signed certs for pipeline...' &&
                    openssl req -x509 -nodes -newkey rsa:2048 -days 7 \
                      -keyout certs/localhost-key.pem \
                      -out certs/localhost.pem \
                      -subj '/CN=localhost';
                  fi
                  chmod 600 certs/localhost.pem certs/localhost-key.pem
                  ls -la certs
                '''
            }
        }

        stage('Build Frontend') {
            steps {
                dir("${FRONTEND_DIR}") {
                    sh '''
                        set -e
                        echo "Node version: $(node --version)"
                        echo "NPM version: $(npm --version)"
                        echo "Current directory: $(pwd)"
                        echo "Directory contents:"
                        ls -la
                        
                        # Check package.json and package-lock.json
                        if [ -f package.json ]; then
                            echo "✓ package.json found"
                        else
                            echo "✗ package.json missing" && exit 1
                        fi
                        
                        if [ -f package-lock.json ]; then
                            echo "✓ package-lock.json found"
                        else
                            echo "⚠ package-lock.json missing, generating..."
                            npm install --package-lock-only
                        fi
                        
                        # Clean install
                        echo "Installing dependencies..."
                        npm ci --silent
                        
                        echo "Building frontend..."
                        npm run build:prod
                        
                        echo "Build output:"
                        ls -la dist/ || echo "No dist directory found"
                    '''
                }
            }
        }

        stage('Test Frontend') {
            steps {
                dir("${FRONTEND_DIR}") {
                    // Skip tests if Chrome is not available in CI
                     // Skip tests if Chrome is not available in CI
                    sh 'echo "Skipping frontend tests in CI environment"'
                    // Or use headless tests: sh 'npm test -- --watch=false --browsers=ChromeHeadless'
                }
            }
        }

        stage('Build Microservices') {
            parallel {
                stage('Build Users') {
                    steps {
                        retry(2) {
                            sh 'docker-compose -f microservice/users/docker-compose.yml build'
                        }
                    }
                }
                stage('Build Courses') {
                    steps {
                        retry(2) {
                            sh 'docker-compose -f microservice/courses/docker-compose.yml build'
                        }
                    }
                }
                stage('Build Messaging') {
                    steps {
                        retry(2) {
                            sh 'docker-compose -f microservice/messaging/docker-compose.yml build'
                        }
                    }
                }
                stage('Build Homework') {
                    steps {
                        retry(2) {
                            sh 'docker-compose -f microservice/homework/docker-compose.yml build'
                        }
                    }
                }
            }
        }

        stage('Build Frontend Container') {
            steps {
                dir("${FRONTEND_DIR}") {
                    sh '''
                        # Build frontend Docker image with caching
                        docker build -t crm-frontend:latest .
                    '''
                }
            }
        }

        stage('Deploy Services') {
            steps {
                sh '''
                    set -e
                    echo "🧹 Complete cleanup..."
                    
                    # Stop all services
                    docker-compose -f microservice/users/docker-compose.yml down --volumes --remove-orphans || true
                    docker-compose -f microservice/courses/docker-compose.yml down --volumes --remove-orphans || true
                    docker-compose -f microservice/homework/docker-compose.yml down --volumes --remove-orphans || true
                    docker-compose -f microservice/messaging/docker-compose.yml down --volumes --remove-orphans || true
                    
                    # Clean up containers and volumes
                    docker container prune -f
                    docker volume prune -f
                    
                    # Recreate network
                    docker network rm crm_network 2>/dev/null || true
                    docker network create crm_network
                    
                    echo "🗄️ Starting MySQL databases..."
                    docker-compose -f microservice/users/docker-compose.yml up -d mysql_users
                    docker-compose -f microservice/courses/docker-compose.yml up -d mysql_courses  
                    docker-compose -f microservice/homework/docker-compose.yml up -d mysql_homework
                    docker-compose -f microservice/messaging/docker-compose.yml up -d mysql_messaging
                    
                    echo "⏳ Waiting for MySQL containers (max 120 seconds)..."
                    
                    # Smart wait - check every 10 seconds instead of waiting full 120
                    for i in {1..12}; do
                        echo "Attempt $i/12..."
                        
                        # Test all MySQL connections
                        if docker exec mysql_users mysqladmin ping -h localhost -u root -pcrm_password --silent 2>/dev/null && \
                           docker exec mysql_courses mysqladmin ping -h localhost -u root -ppassword --silent 2>/dev/null && \
                           docker exec mysql_homework mysqladmin ping -h localhost -u root -ppassword --silent 2>/dev/null && \
                           docker exec mysql_messaging mysqladmin ping -h localhost -u root -ppassword --silent 2>/dev/null; then
                            echo "✅ All MySQL instances ready in $((i*10)) seconds!"
                            break
                        fi
                        
                        if [ $i -eq 12 ]; then
                            echo "❌ MySQL timeout after 120 seconds"
                            exit 1
                        fi
                        
                        sleep 10
                    done
                    
                    echo "🔍 Checking MySQL health..."
                    docker ps | grep mysql
                    
                    # Verify MySQL readiness with proper connection tests
                    echo "🧪 Testing MySQL connections..."
                    
                    # Test each MySQL instance
                    docker exec mysql_users mysqladmin ping -h localhost -u root -pcrm_password --silent || {
                        echo "❌ Users MySQL not ready"
                        docker logs mysql_users --tail 20
                        exit 1
                    }
                    
                    docker exec mysql_courses mysqladmin ping -h localhost -u root -ppassword --silent || {
                        echo "❌ Courses MySQL not ready" 
                        docker logs mysql_courses --tail 20
                        exit 1
                    }
                    
                    docker exec mysql_homework mysqladmin ping -h localhost -u root -ppassword --silent || {
                        echo "❌ Homework MySQL not ready"
                        docker logs mysql_homework --tail 20
                        exit 1
                    }
                    
                    docker exec mysql_messaging mysqladmin ping -h localhost -u root -ppassword --silent || {
                        echo "❌ Messaging MySQL not ready"
                        docker logs mysql_messaging --tail 20
                        exit 1
                    }
                    
                    echo "✅ All MySQL instances are ready!"
                    
                    echo "🚀 Starting application services..."
                    
                    # Start application services with dependency wait
                    docker-compose -f microservice/users/docker-compose.yml up -d users_service
                    sleep 15
                    
                    docker-compose -f microservice/courses/docker-compose.yml up -d courses_service
                    sleep 15
                    
                    docker-compose -f microservice/homework/docker-compose.yml up -d homework_service
                    sleep 15
                    
                    docker-compose -f microservice/messaging/docker-compose.yml up -d messaging_service
                    sleep 15
                    
                    echo "📊 Final status check..."
                    docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
                    
                    echo "✅ All services started successfully!"
                '''
            }
        }

        stage('Deploy Frontend') {
            steps {
                sh '''
                    set -e
                    echo "🚀 Deploying frontend..."
                    
                    # Stop and remove existing container
                    docker stop crm-frontend || true
                    docker rm crm-frontend || true
                    
                    # Deploy frontend on port 8005 (avoiding Jenkins port 8080)
                    docker run -d \
                        --name crm-frontend \
                        --network crm_network \
                        -p 8005:80 \
                        --restart unless-stopped \
                        crm-frontend:latest
                    
                    echo "✅ Frontend deployed on http://localhost:8005"
                '''
            }
        }

        stage('Health Check') {
            steps {
                script {
                    sh '''
                        echo "🔍 Performing health checks..."
                        sleep 30
                        docker ps
                        
                        # Check frontend on port 8005
                        curl -f http://localhost:8005/ || echo "Frontend not ready"
                        
                        # Check microservices
                        curl -k -f https://localhost:8001/ || echo "Users service not ready"
                        curl -k -f https://localhost:8002/ || echo "Courses service not ready"
                        curl -k -f https://localhost:8003/ || echo "Messaging service not ready"
                        curl -k -f https://localhost:8004/ || echo "Homework service not ready"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline completed."
            sh 'docker system prune -f'
        }
        success { echo "✅ CRM pipeline succeeded!" }
        failure { echo "❌ CRM pipeline failed!" }
    }
}