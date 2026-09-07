pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        IMAGE = "mafifdev/devops-demo"
        PROD_HOST = "192.168.123.163"
        KUBE_NAMESPACE = "devops-demo"
        ANSIBLE_CONFIG = "ansible/ansible.cfg"
        LC_ALL = "C.UTF-8"
        LANG = "C.UTF-8"
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
                    docker build --pull \
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

        stage('Deploy to K3s') {
            steps {
                echo "Deploying to K3s with Ansible..."
                sh '''
                    ansible-playbook --version
                    ansible -i ansible/inventory production -m ping

                    ansible-playbook \
                        -i ansible/inventory \
                        ansible/k3s-deploy.yml \
                        -e "image_tag=$BUILD_NUMBER"
                '''
            }
        }

        stage('Deploy to Docker') {
            steps {
                echo "Deploying to Docker with Ansible..."
                sh '''
                    ansible-playbook \
                        -i ansible/inventory \
                        ansible/deploy.yml \
                        -e "image_tag=$BUILD_NUMBER"
                '''
            }
        }

        stage('Health Check Docker') {
            steps {
                echo "Checking Docker application health..."
                sh '''
                    sleep 5
                    curl -f http://$PROD_HOST/health || curl -f http://$PROD_HOST/
                    echo ""
                    echo "Docker application is healthy!"
                '''
            }
        }

        stage('Health Check K3s') {
            steps {
                echo "Checking K3s application health (kubectl + NodePort)..."
                sh '''
                    # 1. Pastikan rollout selesai (lewat Ansible agar reuse SSH inventory)
                    ansible -i ansible/inventory production -m shell -a \
                        "KUBECONFIG=/home/devops/.kube/config kubectl rollout status deployment/devops-demo -n $KUBE_NAMESPACE --timeout=120s"

                    # 2. Ambil NodePort service secara dinamis
                    NODE_PORT=$(ansible -i ansible/inventory production -m shell -a \
                        "KUBECONFIG=/home/devops/.kube/config kubectl get svc devops-demo -n $KUBE_NAMESPACE -o jsonpath={.spec.ports[0].nodePort}" \
                        | grep -oE '[0-9]{4,5}' | tail -1)

                    echo "K3s NodePort: $NODE_PORT"

                    if [ -z "$NODE_PORT" ]; then
                        echo "ERROR: gagal mendapatkan NodePort service devops-demo"
                        exit 1
                    fi

                    # 3. Curl ke NodePort dari sisi prod-server (via Ansible, tanpa butuh kubeconfig di Jenkins)
                    ansible -i ansible/inventory production -m shell -a \
                        "curl -f http://127.0.0.1:$NODE_PORT/health || curl -f http://127.0.0.1:$NODE_PORT/"

                    echo ""
                    echo "K3s application is healthy on NodePort $NODE_PORT!"
                '''
            }
        }
    }

    post {
        success {
            echo "Deployment successful! Docker: http://$PROD_HOST/health, K3s: NodePort (see Health Check K3s log)."
        }
        failure {
            echo "Pipeline failed! Cek stage mana yang merah: build/push/deploy/health."
        }
        always {
            sh 'docker logout || true'
        }
    }
}
