pipeline {
    agent any
    
    environment {
        DOCKER_BUILDKIT = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
        CERTS_PATH = "${env.WORKSPACE}"
    }
    triggers {
        githubPush()
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
                    echo "🔒 Preparing SSL certificates for Docker volume..."

                    # Create the Docker volume if it doesn't exist mounting
                    docker volume create certs_volume || true
                    echo "pathPwd ${PWD}"
                    ls -la "${PWD}"
                    # Create a temporary container to copy files to the volume
                    docker run --rm -v certs_volume:/certs -v "${PWD}" alpine sh -c "
                        if [ ! -f /certs/localhost.pem ] || [ ! -f /certs/localhost-key.pem ]; then
                            echo 'Copying SSL certificates to volume...'
                            cp "${PWD}":/localhost.pem /certs/ 2>/dev/null || echo 'localhost.pem not found in root directory'
                            cp "${PWD}":/localhost-key.pem /certs/ 2>/dev/null || echo 'localhost-key.pem not found in root directory'
                            chmod 600 /certs/localhost.pem /certs/localhost-key.pem 2>/dev/null || true
                        else
                            echo 'SSL certificates already exist in volume'
                        fi
                        echo 'Contents of certs volume:'
                        ls -la /certs/
                    "
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
                    pwd
                    echo "certs ls before"
                    ls -l certs
                    echo "🧹 Cleaning up existing containers..."
                    docker-compose -f microservice/users/docker-compose.yml down || true
                    docker-compose -f microservice/courses/docker-compose.yml down || true
                    docker-compose -f microservice/homework/docker-compose.yml down || true
                    docker-compose -f microservice/messaging/docker-compose.yml down || true
                    
                   
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
                    pwd
                    echo "CERTS_PATH is: $CERTS_PATH"
                    echo "certs ls after"
                    ls -l certs
                    echo "✅ All services started :)"
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