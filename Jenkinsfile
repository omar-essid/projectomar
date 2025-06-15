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
                    dockerImage = docker.build("${registry}:latest")
                }
            }
        }

        stage('Scan Docker Image with Trivy') {
            steps {
                script {
                    // Vérifie si le dossier cache db Trivy existe
                    def dbFilesExist = sh(script: "test -d ${env.TRIVY_CACHE_DIR}/db", returnStatus: true) == 0

                    if (!dbFilesExist) {
                        echo "⚠️ Base Trivy absente dans ${env.TRIVY_CACHE_DIR}. Le scan est ignoré. Téléchargez-la manuellement si nécessaire."
                    } else {
                        sh """
                            trivy image \
                            --timeout 10m \
                            --cache-dir ${env.TRIVY_CACHE_DIR} \
                            --skip-update \
                            --format table \
                            --scanners vuln \
                            --exit-code 0 \
                            --severity HIGH,CRITICAL \
                            ${registry}:latest
                        """
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    echo "📦 Pushing Docker image to Docker Hub"
                    // Utiliser avec précaution la gestion des secrets (voir Jenkins Credentials pour sécuriser)
                    sh '''
                        echo "$DOCKERHUB_PASSWORD" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
                        docker tag ${registry}:latest ${registry}:latest
                        docker push ${registry}:latest
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                script {
                    sh '''
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 "minikube start"
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 'kubectl config use-context minikube'
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 'kubectl apply -f /root/project/docker-spring-boot/deployment.yaml'
                    '''
                }
            }
        }

        stage('🗂️ Collect Logs and Snapshot') {
            steps {
                script {
                    echo "🛠️ Collecting Jenkins logs, Trivy results, and Minikube snapshot"
                    sh "bash collect_full_logs.sh"
                }
            }
        }

        stage('🧠 AI Analysis of Logs') {
            steps {
                script {
                    echo "🤖 Running AI script for full_logs.log analysis"
                    sh "python3 script-model-ai-codet5-codebert.py"
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline terminé avec succès."
        }
        failure {
            echo "❌ Échec du pipeline. Vérifiez les logs."
        }
    }
}
