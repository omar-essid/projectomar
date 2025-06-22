pipeline {
    agent any

    environment {
        registry = "omarpfe/projectpfe"
        registryCredential = 'dockerhub'
        SONAR_TOKEN = credentials('jenkins-sonar')
        TRIVY_CACHE_DIR = '/trivy-cache'  // Volume persistant
    }

    tools {
        maven 'M2_HOME'
    }

    stages {
        stage('Checkout Git') {
            steps {
                git url: 'https://github.com/omar-essid/projectomar.git', branch: 'main', credentialsId: 'github-omar-token'
            }
        }

        stage('Clean') {
            steps {
                sh "mvn clean"
            }
        }

        stage('Compile') {
            steps {
                sh "mvn compile"
            }
        }

        stage('Package') {
            steps {
                sh "mvn package -Dmaven.test.skip=true"
            }
        }

        stage('Tests') {
            steps {
                sh "mvn test"
            }
        }

        stage('Analyse SonarQube') {
            steps {
                withSonarQubeEnv('sq1') {
                    withEnv(["SONAR_TOKEN=${env.SONAR_TOKEN}"]) {
                        sh "mvn org.sonarsource.scanner.maven:sonar-maven-plugin:3.9.0.2155:sonar"
                    }
                }
            }
        }

        stage('Deploy to Nexus') {
            steps {
                sh 'mvn deploy'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${registry}:latest")
                }
            }
        }

        stage('Initialize Trivy') {
            steps {
                script {
                    sh "mkdir -p ${TRIVY_CACHE_DIR}"
                    // Nouvelle approche pour Trivy 0.56.0+
                    sh """
                        docker run --rm \
                            -v ${TRIVY_CACHE_DIR}:/root/.cache \
                            aquasec/trivy:latest \
                            trivy image --cache-dir /root/.cache --download-db-only alpine:latest || \
                            echo "Initialisation du cache Trivy (peut échouer sur les nouvelles versions)"
                    """
                }
            }
        }

        stage('Scan Docker Image with Trivy') {
            steps {
                script {
                    sh """
                        docker run --rm \
                            -v ${TRIVY_CACHE_DIR}:/root/.cache \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy:latest \
                            trivy image \
                            --cache-dir /root/.cache \
                            --no-progress \
                            --format table \
                            --security-checks vuln \
                            --exit-code 0 \
                            --severity HIGH,CRITICAL \
                            ${registry}:latest
                    """
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PWD')]) {
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
                script {
                    sshagent(credentials: ['minikube-ssh']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no omar@192.168.88.131 \
                                "minikube start && \
                                kubectl config use-context minikube && \
                                kubectl apply -f /root/project/docker-spring-boot/deployment.yaml"
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline exécuté avec succès"
        }
        failure {
            echo "❌ Échec du pipeline"
        }
    }
}
