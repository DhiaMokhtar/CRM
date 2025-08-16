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
                    mkdir -p certs
                    # Ensure certs exist (if already in certs/ do NOT copy duplicates silently)
                    if [ -f localhost.pem ] && [ -f localhost-key.pem ]; then
                      cp -n localhost.pem certs/ || true
                      cp -n localhost-key.pem certs/ || true
                    fi
                    echo "Listing root certs dir:"
                    ls -la certs/
                    test -s certs/localhost.pem
                    test -s certs/localhost-key.pem
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
                    echo "Waiting for services to be ready..."
                    sleep 30
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