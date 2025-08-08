pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git credentialsId: 'crm', url: 'https://github.com/DhiaMokhtar/CRM.git', branch: 'services'
            }
        }

        stage('Backend: Install Dependencies') {
            steps {
                dir('backend') {
                    sh 'pip install -r requirements.txt'
                }
            }
        }

        stage('Backend: Test') {
            steps {
                dir('backend') {
                    sh 'python manage.py test'
                }
            }
        }

        stage('Frontend: Install Dependencies') {
            steps {
                dir('frontend') {
                    sh 'npm ci'
                }
            }
        }

        stage('Frontend: Test') {
            steps {
                dir('frontend') {
                    sh 'npm run test -- --watch=false'
                }
            }
        }

        stage('Frontend: Build') {
            steps {
                dir('frontend') {
                    sh 'npm run build -- --configuration=production'
                }
            }
        }

        stage('Collect Static') {
            steps {
                sh 'cp -r frontend/dist/* backend/static/'
                dir('backend') {
                    sh 'python manage.py collectstatic --noinput'
                }
            }
        }

        stage('Deploy') {
            steps {
                // Your deployment steps here
                // Example: restart app server
                //change for test
                sh 'sudo systemctl restart gunicorn'
                sh 'sudo systemctl restart nginx'
            }
        }
    }
}