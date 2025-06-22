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
        stage('Checkout Git') {
            steps {
                git url: 'https://github.com/omar-essid/projectomar.git', 
                     branch: 'main', 
                     credentialsId: 'github-omar-token'
            }
        }

        stage('Build et Tests') {
            steps {
                sh "mvn clean package -Dmaven.test.skip=true"
                sh "mvn test"
            }
        }

        stage('Analyse SonarQube') {
            steps {
                withSonarQubeEnv('sq1') {
                    sh "mvn sonar:sonar -Dsonar.login=${env.SONAR_TOKEN}"
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

        stage('Scan Sécurité Trivy') {
            steps {
                script {
                    sh """
                        mkdir -p ${TRIVY_CACHE_DIR}
                        if [ ! -f "${TRIVY_CACHE_DIR}/db/metadata.json" ] || \\
                           [ "\$(find "${TRIVY_CACHE_DIR}/db/metadata.json" -mtime +0)" ]; then
                            trivy --cache-dir ${TRIVY_CACHE_DIR} image --download-db-only
                        fi
                    """
                    
                    sh """
                        trivy image \
                            --cache-dir ${TRIVY_CACHE_DIR} \
                            --skip-update \
                            --format table \
                            --severity HIGH,CRITICAL \
                            --exit-code 0 \
                            ${registry}:latest
                    """
                }
            }
        }

        stage('Déploiement Docker Hub') {
            steps {
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

        stage('Déploiement Minikube') {
            steps {
                sshagent(['minikube-ssh']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no omar@192.168.88.131 \
                            "kubectl config use-context minikube && \\
                             kubectl apply -f /root/project/docker-spring-boot/deployment.yaml"
                    """
                }
            }
        }
    }

    post {
        success {
            echo 'Déploiement réussi'
            slackSend color: 'good', 
                     message: "SUCCÈS: Build ${env.BUILD_NUMBER} déployé"
        }
        failure {
            echo 'Échec du pipeline'
            slackSend color: 'danger', 
                     message: "ÉCHEC: Build ${env.BUILD_NUMBER} a échoué"
        }
        always {
            cleanWs()
        }
    }
}
