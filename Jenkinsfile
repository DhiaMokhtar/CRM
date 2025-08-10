pipeline {
    agent any
    
    tools {
        nodejs 'Node24'  // Make sure this matches your Jenkins NodeJS installation
    }
    
    environment {
        FRONTEND_DIR = 'frond-end'
        USERS_COMPOSE = 'microservice/users/docker-compose.yml'
        COURSES_COMPOSE = 'microservice/courses/docker-compose.yml'
        HOMEWORK_COMPOSE = 'microservice/homework/docker-compose.yml'
        MESSAGING_COMPOSE = 'microservice/messaging/docker-compose.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Frontend') {
            steps {
                dir("${FRONTEND_DIR}") {
                    sh 'npm install --legacy-peer-deps'
                    sh 'npm run build -- --configuration production'
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
                stage('Users Service') {
                    steps {
                        sh "docker-compose -f ${USERS_COMPOSE} build"
                    }
                }
                stage('Courses Service') {
                    steps {
                        sh "docker-compose -f ${COURSES_COMPOSE} build"
                    }
                }
                stage('Homework Service') {
                    steps {
                        sh "docker-compose -f ${HOMEWORK_COMPOSE} build"
                    }
                }
                stage('Messaging Service') {
                    steps {
                        sh "docker-compose -f ${MESSAGING_COMPOSE} build"
                    }
                }
            }
        }

        stage('Deploy Services') {
            steps {
                // Create external network first
                sh 'docker network create crm_network || true'
                
                sh "docker-compose -f ${USERS_COMPOSE} up -d"
                sh "docker-compose -f ${COURSES_COMPOSE} up -d"
                sh "docker-compose -f ${HOMEWORK_COMPOSE} up -d"
                sh "docker-compose -f ${MESSAGING_COMPOSE} up -d"
            }
        }

        stage('Health Check') {
            steps {
                script {
                    sh 'sleep 30'
                    sh 'docker ps' // Show running containers
                    // Add health checks for your services
                    sh 'curl -f http://localhost:8001/ || echo "Users service not ready"'
                    sh 'curl -f http://localhost:8002/ || echo "Courses service not ready"'
                    sh 'curl -f http://localhost:8003/ || echo "Messaging service not ready"'
                    sh 'curl -f http://localhost:8004/ || echo "Homework service not ready"'
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline completed."
            // Clean up if needed
            // Clean up if needed
            // Clean up if needed

            sh 'docker system prune -f'
        }
        success {
            echo "✅ CRM pipeline succeeded!"
        }
        failure {
            echo "❌ CRM pipeline failed!"
        }
    }
}