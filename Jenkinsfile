pipeline {
    agent any

    environment {
        registry = "omarpfe/projectpfe"
        registryCredential = 'dockerhub'
        SONAR_TOKEN = credentials('jenkins-sonar')
        TRIVY_CACHE_DIR = '/home/jenkins/trivy-cache'
    }

    tools {
        maven 'M2_HOME'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'mvn clean package -Dmaven.test.skip=true'
            }
        }

        stage('Tests') {
            steps {
                sh 'mvn test'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sq1') {
                    sh "mvn sonar:sonar -Dsonar.login=${SONAR_TOKEN}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${registry}:latest")
                }
            }
        }

        stage('Security Scan') {
            steps {
                script {
                    sh """
                        mkdir -p ${TRIVY_CACHE_DIR}
                        trivy --cache-dir ${TRIVY_CACHE_DIR} image --skip-db-update --scanners vuln --severity HIGH,CRITICAL --exit-code 0 ${registry}:latest
                    """
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'dockerhub',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PWD'
                    )]) {
                        sh """
                            docker login -u $DOCKER_USER -p $DOCKER_PWD
                            docker push ${registry}:latest
                        """
                    }
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sshagent(['minikube-ssh']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no omar@192.168.88.131 \
                            "kubectl config use-context minikube && \
                             kubectl apply -f /root/project/docker-spring-boot/deployment.yaml"
                    """
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            slackSend color: 'good', message: "SUCCESS: Build ${env.BUILD_NUMBER}"
        }
        failure {
            slackSend color: 'danger', message: "FAILED: Build ${env.BUILD_NUMBER}"
        }
    }
}
