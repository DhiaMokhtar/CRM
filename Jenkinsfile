pipeline {
    agent any
    
    environment {
        DOCKER_BUILDKIT = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '🔄 Checking out code...'
                checkout scm
            }
        }
        
        stage('Prepare SSL certs') {
            steps {
                sh '''
                    echo "🔐 Preparing SSL certificates..."
                    
                    # Ensure certs directory exists
                    mkdir -p certs
                    

                    # Copy certificates from root to certs directory
                    if [ -f localhost.pem ] && [ -f localhost-key.pem ]; then
                        echo "Copying certificates from root to certs/"
                        cp localhost.pem certs/
                        cp localhost-key.pem certs/
                    else
                        echo "ERROR: Certificates not found in root"
                        ls -la ./
                        exit 1
                    fi
                    
                    # Verify certificates are properly copied
                    echo "Verifying certificates in certs/:"
                    ls -la certs/
                    
                    if [ ! -s certs/localhost.pem ] || [ ! -s certs/localhost-key.pem ]; then
                        echo "ERROR: Certificates are missing or empty in certs/"
                        exit 1
                    fi
                    
                    echo "✅ Certificates ready for deployment"
                '''
            }
        }
        
        stage('Build Microservices') {
            parallel {
                stage('Build Users Service') {
                    steps {
                        echo '🏗️ Building Users Service...'
                        sh 'docker-compose -f microservice/users/docker-compose.yml build'
                    }
                }
                stage('Build Courses Service') {
                    steps {
                        echo '🏗️ Building Courses Service...'
                        sh 'docker-compose -f microservice/courses/docker-compose.yml build'
                    }
                }
                stage('Build Homework Service') {
                    steps {
                        echo '🏗️ Building Homework Service...'
                        sh 'docker-compose -f microservice/homework/docker-compose.yml build'
                    }
                }
                stage('Build Messaging Service') {
                    steps {
                        echo '🏗️ Building Messaging Service...'
                        sh 'docker-compose -f microservice/messaging/docker-compose.yml build'
                    }
                }
            }
        }
        
        stage('Deploy Services') {
            steps {
                sh '''
                    echo "🧹 Cleaning up existing containers..."
                    docker-compose -f microservice/users/docker-compose.yml down -v || true
                    docker-compose -f microservice/courses/docker-compose.yml down -v || true
                    docker-compose -f microservice/homework/docker-compose.yml down -v || true
                    docker-compose -f microservice/messaging/docker-compose.yml down -v || true
                    

                    docker container prune -f
                    docker volume prune -f
                    docker network rm crm_network || true
                    docker network create crm_network
                    
                    echo "🔍 Final verification of certificates before deployment:"
                    ls -la certs/
                    if [ ! -s certs/localhost.pem ] || [ ! -s certs/localhost-key.pem ]; then
                        echo "ERROR: Certificates missing before deployment!"
                        exit 1
                    fi
                    
                    # Copy certs to /tmp which is accessible by Docker
                    echo "📁 Copying certificates to Docker-accessible location..."
                    sudo mkdir -p /tmp/crm-certs
                    sudo cp certs/localhost.pem /tmp/crm-certs/
                    sudo cp certs/localhost-key.pem /tmp/crm-certs/
                    sudo chmod 644 /tmp/crm-certs/*
                    
                    echo "🔍 Verifying certificates in /tmp/crm-certs:"
                    ls -la /tmp/crm-certs/
                    
                    echo "🔍 Testing certificate mount with /tmp path:"
                    docker run --rm -v /tmp/crm-certs:/test-mount:ro alpine ls -la /test-mount/
                    
                    echo "🚀 Starting MySQL databases first..."
                    CERT_PATH=/tmp/crm-certs docker-compose -f microservice/users/docker-compose.yml up -d mysql_users
                    CERT_PATH=/tmp/crm-certs docker-compose -f microservice/courses/docker-compose.yml up -d mysql_courses
                    CERT_PATH=/tmp/crm-certs docker-compose -f microservice/homework/docker-compose.yml up -d mysql_homework
                    CERT_PATH=/tmp/crm-certs docker-compose -f microservice/messaging/docker-compose.yml up -d mysql_messaging
                    
                    echo "⏳ Waiting for MySQL containers to initialize..."
                    sleep 60
                    
                    echo "🚀 Starting application services..."
                    CERT_PATH=/tmp/crm-certs docker-compose -f microservice/users/docker-compose.yml up -d users_service
                    
                    echo "🔍 Debugging: Check if certificates are accessible in container:"
                    sleep 10
                    docker exec users_service ls -la /certs-in/ || echo "Mount failed"
                    
                    CERT_PATH=/tmp/crm-certs docker-compose -f microservice/courses/docker-compose.yml up -d courses_service
                    CERT_PATH=/tmp/crm-certs docker-compose -f microservice/homework/docker-compose.yml up -d homework_service
                    CERT_PATH=/tmp/crm-certs docker-compose -f microservice/messaging/docker-compose.yml up -d messaging_service
                    
                    echo "✅ All services started"
                '''
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    echo '🔍 Performing health checks...'
                    sh 'docker ps'
                    
                    sh '''
                        echo "Checking microservices with HTTPS..."
                        curl -k -f https://localhost:8001/api/health/ || echo "Users service health check failed"
                        curl -k -f https://localhost:8002/api/health/ || echo "Courses service health check failed"
                        curl -k -f https://localhost:8003/api/health/ || echo "Messaging service health check failed"
                        curl -k -f https://localhost:8004/api/health/ || echo "Homework service health check failed"
                        
                        echo "Checking container logs..."
                        docker logs users_service --tail=10 || true
                        docker logs courses_service --tail=10 || true
                        docker logs homework_service --tail=10 || true
                        docker logs messaging_service --tail=10 || true
                    '''
                }
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline completed.'
            sh 'docker system prune -f'
        }
        success {
            echo '✅ CRM pipeline succeeded!'
            echo 'Microservices available at:'
            echo '- Users: https://localhost:8001'
            echo '- Courses: https://localhost:8002' 
            echo '- Messaging: https://localhost:8003'
            echo '- Homework: https://localhost:8004'
            echo ''
            echo 'To run frontend locally:'
            echo 'cd frond-end && ng serve --ssl --ssl-key ssl/key.pem --ssl-cert ssl/cert.pem'
        }
        failure {
            echo '❌ CRM pipeline failed!'
            sh '''
                echo "Service logs for debugging:"
                docker logs mysql_users --tail=20 || true
                docker logs mysql_courses --tail=20 || true
                docker logs mysql_homework --tail=20 || true
                docker logs mysql_messaging --tail=20 || true
                docker logs users_service --tail=20 || true
                docker logs courses_service --tail=20 || true
                docker logs homework_service --tail=20 || true
                docker logs messaging_service --tail=20 || true
            '''
        }
    }
}