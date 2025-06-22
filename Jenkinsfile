pipeline {
    agent any

    environment {
        registry = "omarpfe/projectpfe"
        registryCredential = 'dockerhub'
        SONAR_TOKEN = credentials('jenkins-sonar')
        TRIVY_CACHE_DIR = '/trivy-cache'  # Volume persistant
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
                    def dockerImage = docker.build("${registry}:latest")  # Correction: ajout de 'def'
                }
            }
        }

        stage('Setup Trivy Cache') {
            steps {
                script {
                    // Crée le dossier cache si inexistant
                    sh "mkdir -p ${TRIVY_CACHE_DIR}"
                    
                    // Vérifie si la DB existe déjà
                    def dbExists = sh(script: "test -f ${TRIVY_CACHE_DIR}/db/metadata.json", returnStatus: true) == 0
                    
                    if (!dbExists) {
                        echo "🔵 Initialisation du cache Trivy (première exécution)"
                        sh """
                            docker run --rm \
                                -v ${TRIVY_CACHE_DIR}:/root/.cache \
                                aquasec/trivy:latest \
                                trivy image --download-db-only --cache-dir /root/.cache || echo "⚠️ Ignoré si la commande échoue avec les nouvelles versions"
                        """
                    } else {
                        echo "🟢 Cache Trivy déjà initialisé"
                    }
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
                            --skip-db-update \
                            --skip-java-db-update \
                            --no-progress \
                            --format table \
                            --scanners vuln \
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

        stage('Collect Full Logs') {
            steps {
                script {
                    sshagent(credentials: ['minikube-ssh']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no omar@192.168.88.131 \
                                "cd /root/project/docker-spring-boot && \
                                bash collect_full_logs.sh"
                        """
                    }
                }
            }
        }

        stage('Analyse IA avec CodeT5 & CodeBERT') {
            steps {
                script {
                    sshagent(credentials: ['minikube-ssh']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no omar@192.168.88.131 \
                                "cd /root/project/docker-spring-boot && \
                                python3 script-model-ai-codet5-codebert.py full_logs.log"
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline exécuté avec succès"
            slackSend(color: 'good', message: "Build SUCCEEDED: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
        failure {
            echo "❌ Échec du pipeline"
            slackSend(color: 'danger', message: "Build FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
        always {
            cleanWs()  # Nettoyage du workspace
        }
    }
}
