pipeline {
    agent any

    environment {
        IMAGE = "mafifdev/devops-demo"
        PROD_HOST = "192.168.123.163"
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Test') {
            steps {
                echo 'Running application test...'

                sh '''
                    python3 --version
                    docker --version

                    python3 -m py_compile app.py
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Docker image..."

                sh '''
                    docker build \
                        -t $IMAGE:$BUILD_NUMBER \
                        -t $IMAGE:latest \
                        .
                '''
            }
        }

        stage('Docker Push') {
            steps {
                echo "Pushing Docker image to Docker Hub..."

                withCredentials([
                    usernamePassword(
                        credentialsId: 'mafifdev',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {

                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login \
                            --username "$DOCKER_USER" \
                            --password-stdin

                        docker push $IMAGE:$BUILD_NUMBER
                        docker push $IMAGE:latest

                        docker logout
                    '''
                }
            }
        }

        stage('Ansible Deploy') {
            steps {
                echo "Deploying to production with Ansible..."

                sh '''
                    export LC_ALL=C.UTF-8
                    export LANG=C.UTF-8
                    export LANGUAGE=C.UTF-8
                    export ANSIBLE_CONFIG=ansible/ansible.cfg

                    locale -a || true
                    ansible-playbook --version

                    ansible-playbook \
                        -i ansible/inventory \
                        ansible/deploy.yml \
                        -e "image_tag=$BUILD_NUMBER"
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo "Checking application health..."

                sh '''
                    sleep 5

                    curl -f http://$PROD_HOST/health || \
                    curl -f http://$PROD_HOST/

                    echo ""
                    echo "Application is healthy!"
                '''
            }
        }
    }

    post {
        success {
            echo "Deployment successful!"
        }

        failure {
            echo "Pipeline failed!"
        }

        always {
            sh 'docker logout || true'
        }
    }
}
