pipeline {
    agent any
    
    tools {
        nodejs 'Node18'  // Use the name you configured
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
                    sh 'npm install'
                    sh 'npm run build -- --configuration production'
                }
            }
        }

        stage('Test Frontend') {
            steps {
                dir("${FRONTEND_DIR}") {
                    sh 'npm test -- --watch=false --browsers=ChromeHeadless'
                }
            }
        }

        stage('Build & Test Microservices') {
            parallel {
                stage('Users Service') {
                    steps {
                        sh "docker-compose -f ${USERS_COMPOSE} build"
                        // Optionally run Django tests:
                        // sh "docker-compose -f ${USERS_COMPOSE} run users_service python manage.py test"
                    }
                }
                stage('Courses Service') {
                    steps {
                        sh "docker-compose -f ${COURSES_COMPOSE} build"
                        // Optionally run Django tests:
                        // sh "docker-compose -f ${COURSES_COMPOSE} run courses_service python manage.py test"
                    }
                }
                stage('Homework Service') {
                    steps {
                        sh "docker-compose -f ${HOMEWORK_COMPOSE} build"
                        // Optionally run Django tests:
                        // sh "docker-compose -f ${HOMEWORK_COMPOSE} run homework_service python manage.py test"
                    }
                }
                stage('Messaging Service') {
                    steps {
                        sh "docker-compose -f ${MESSAGING_COMPOSE} build"
                        // Optionally run Django tests:
                        // sh "docker-compose -f ${MESSAGING_COMPOSE} run messaging_service python manage.py test"
                    }
                }
            }
        }

        stage('Deploy All Services') {
            steps {
                sh "docker-compose -f ${USERS_COMPOSE} up -d"
                sh "docker-compose -f ${COURSES_COMPOSE} up -d"
                sh "docker-compose -f ${HOMEWORK_COMPOSE} up -d"
                sh "docker-compose -f ${MESSAGING_COMPOSE} up -d"
            }
        }

        stage('Health Check') {
            steps {
                script {
                    sh 'sleep 30' // Wait for services to start
                    sh 'curl -f http://localhost:8001/health || exit 1' // Users service
                    sh 'curl -f http://localhost:8002/health || exit 1' // Courses service
                    // Add other service health checks
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline finished."
        }
        success {
            slackSend(channel: '#deployments', message: "✅ CRM pipeline succeeded!")
        }
        failure {
            echo "Pipeline failed."
            slackSend(channel: '#deployments', message: "❌ CRM pipeline failed!")
        }
    }
}