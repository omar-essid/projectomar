pipeline {
    agent any

    environment {
        registry = "omarpfe/projectpfe"
        registryCredential = 'dockerhub'
        SONAR_TOKEN = credentials('jenkins-sonar')
        TRIVY_CACHE_DIR = '/trivy-cache'  // Volume persistant pour le cache
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

        stage('Initialiser Cache Trivy (Une fois)') {
            steps {
                script {
                    // Vérifie si la DB existe déjà
                    def dbExists = sh(script: """
                        if [ -f "${TRIVY_CACHE_DIR}/db/metadata.json" ]; then 
                            exit 0
                        else 
                            exit 1
                        fi
                    """, returnStatus: true) == 0
                    
                    if (!dbExists) {
                        echo "⚠️ Téléchargement initial de la DB Trivy (seulement à la première exécution)"
                        sh """
                            mkdir -p ${TRIVY_CACHE_DIR}
                            docker run --rm \
                                -v ${TRIVY_CACHE_DIR}:/root/.cache \
                                aquasec/trivy:latest \
                                trivy db --download-db-only --cache-dir /root/.cache
                        """
                    } else {
                        echo "✅ Cache Trivy déjà initialisé (pas de téléchargement)"
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
                    echo "Push Docker avec commande shell manuelle"
                    sh '''
                        docker login -u omarpfe -p 'kd8CB%4CfH&hDkk'
                        docker tag omarpfe/projectpfe:latest omarpfe/projectpfe:latest
                        docker push omarpfe/projectpfe:latest
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

        stage('Collect Full Logs') {
            steps {
                script {
                    echo "📦 Collecte des logs Jenkins, Trivy et configuration pod..."
                    sh '''
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 '
                            cd /root/project/docker-spring-boot &&
                            bash collect_full_logs.sh
                        '
                    '''
                }
            }
        }

        stage('Analyse IA avec CodeT5 & CodeBERT') {
            steps {
                script {
                    echo "🤖 Exécution du script IA sur le fichier full_logs.log..."
                    sh '''
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 '
                            cd /root/project/docker-spring-boot &&
                            python3 script-model-ai-codet5-codebert.py full_logs.log
                        '
                    '''
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
