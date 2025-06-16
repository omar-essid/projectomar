pipeline {
    agent any

    environment {
        REGISTRY = "omarpfe/projectpfe"
        DOCKER_CREDENTIALS = 'dockerHub'       // Id des credentials Jenkins Docker Hub
        TRIVY_CACHE = "/opt/trivy/cache"
        IMAGE_TAG = "${REGISTRY}:latest"
    }

    stages {
        stage('Build Docker Image') {
            steps {
                echo "🔨 Build Docker image"
                script {
                    dockerImage = docker.build("${IMAGE_TAG}")
                }
            }
        }

        stage('Prepare Trivy Cache') {
            steps {
                echo "📁 Préparation du cache Trivy"
                // Si le dossier de cache n'existe pas, on le crée
                sh '''
                    if [ ! -d "${TRIVY_CACHE}" ]; then
                        mkdir -p ${TRIVY_CACHE}
                    fi
                    # On fait un premier scan simple pour initialiser la DB (éviter l'erreur skip-db-update sur premier run)
                    if [ ! -f "${TRIVY_CACHE}/trivy.db" ]; then
                        trivy image --cache-dir ${TRIVY_CACHE} --format table --severity HIGH,CRITICAL alpine:latest
                    fi
                '''
            }
        }

        stage('Scan Docker Image with Trivy') {
            steps {
                echo "🔍 Analyse vulnérabilités avec Trivy"
                sh """
                    trivy image --cache-dir ${TRIVY_CACHE} --format table --scanners vuln --severity HIGH,CRITICAL ${IMAGE_TAG} || true
                """
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                echo "📦 Push de l'image Docker vers Docker Hub"
                script {
                    docker.withRegistry('https://registry.hub.docker.com', DOCKER_CREDENTIALS) {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                echo "🚀 Déploiement sur Minikube"
                // Exemple simple, adapter selon ton déploiement
                sh '''
                    kubectl apply -f k8s/deployment.yaml
                    kubectl rollout status deployment/my-deployment
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline terminé avec succès"
        }
        failure {
            echo "❌ Pipeline échoué"
        }
    }
}
