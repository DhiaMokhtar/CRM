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
                    set -e
                    mkdir -p certs
                    # Copy certificates to shared location
                    if [ ! -f certs/localhost.pem ] || [ ! -f certs/localhost-key.pem ]; then
                        cp localhost.pem certs/ || true
                        cp localhost-key.pem certs/ || true
                    fi
                    chmod 600 certs/localhost.pem certs/localhost-key.pem
                    ls -la certs
                    
                    # Verify certificates exist
                    if [ -f certs/localhost.pem ] && [ -f certs/localhost-key.pem ]; then
                        echo "✓ Certificates ready for sharing"
                    else
                        echo "❌ Certificates missing - services will generate individual certs"
                    fi
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
                    
                    echo "🚀 Starting MySQL databases first..."
                    docker-compose -f microservice/users/docker-compose.yml up -d mysql_users
                    docker-compose -f microservice/courses/docker-compose.yml up -d mysql_courses
                    docker-compose -f microservice/homework/docker-compose.yml up -d mysql_homework
                    docker-compose -f microservice/messaging/docker-compose.yml up -d mysql_messaging
                    echo "⏳ Waiting 60 seconds for MySQL containers to initialize..."
                    sleep 60
                    docker ps
                    
                    echo "🚀 Starting application services..."
                    docker-compose -f microservice/users/docker-compose.yml up -d users_service
                    docker-compose -f microservice/courses/docker-compose.yml up -d courses_service
                    docker-compose -f microservice/homework/docker-compose.yml up -d homework_service
                    docker-compose -f microservice/messaging/docker-compose.yml up -d messaging_service
                    
                    echo "✅ All services started"
                '''
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    echo '🔍 Performing health checks...'
                    sh 'sleep 30'
                    sh 'docker ps'
                    
                    sh '''
                        echo "Checking microservices..."
                        curl -f http://localhost:8001/ || echo "Users service not ready"
                        curl -f http://localhost:8002/ || echo "Courses service not ready"
                        curl -f http://localhost:8003/ || echo "Messaging service not ready"
                        curl -f http://localhost:8004/ || echo "Homework service not ready"
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
        }
        failure {
            echo '❌ CRM pipeline failed!'
            sh '''
                echo "Service logs for debugging:"
                docker logs mysql_users || true
                docker logs mysql_courses || true
                docker logs mysql_homework || true
                docker logs mysql_messaging || true
                docker logs users_service || true
                docker logs courses_service || true
                docker logs homework_service || true
                docker logs messaging_service || true
            '''
        }
    }
}