pipeline {
    agent any

    environment {
        DOCKER_BUILDKIT = 1
        FRONTEND_DIR = 'frond-end'
        USERS_COMPOSE = 'microservice/docker-compose(users).yml'
        COURSES_COMPOSE = 'microservice/docker-compose(courses).yml'
        HOMEWORK_COMPOSE = 'microservice/docker-compose(homework).yml'
        MESSAGING_COMPOSE = 'microservice/docker-compose(messaging).yml'
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

        stage('Build & Test Microservices') {
            parallel {
                stage('Users Service') {
                    steps {
                        sh 'docker-compose -f ${USERS_COMPOSE} build'
                        // Add test commands if available, e.g.:
                        // sh 'docker-compose -f ${USERS_COMPOSE} run users_service pytest'
                    }
                }
                stage('Courses Service') {
                    steps {
                        sh 'docker-compose -f ${COURSES_COMPOSE} build'
                        // Add test commands if available
                    }
                }
                stage('Homework Service') {
                    steps {
                        sh 'docker-compose -f ${HOMEWORK_COMPOSE} build'
                        // Add test commands if available
                    }
                }
                stage('Messaging Service') {
                    steps {
                        sh 'docker-compose -f ${MESSAGING_COMPOSE} build'
                        // Add test commands if available
                    }
                }
            }
        }

        stage('Deploy Microservices') {
            steps {
                sh 'docker-compose -f ${USERS_COMPOSE} up -d'
                sh 'docker-compose -f ${COURSES_COMPOSE} up -d'
                sh 'docker-compose -f ${HOMEWORK_COMPOSE} up -d'
                sh 'docker-compose -f ${MESSAGING_COMPOSE} up -d'
            }
        }

        stage('Push Docker Images') {
            steps {
                // Example: Push images to Docker registry (replace with your registry)
                // sh 'docker tag users_service your-registry/users_service:latest'
                // sh 'docker push your-registry/users_service:latest'
                // Repeat for other services
            }
        }
    }

    post {
        always {
            echo "Pipeline finished."
        }
        success {
            // Example: Slack notification (requires Slack plugin)
            // slackSend(channel: '#deployments', message: "CRM pipeline succeeded!")
        }
        failure {
            echo "Pipeline failed."
            // slackSend(channel: '#deployments', message: "CRM pipeline failed!")
        }
    }
}