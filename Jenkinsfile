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
        // [Toutes vos étapes existantes jusqu'à Build Docker Image...]

        stage('Initialize Trivy Cache') {
            steps {
                script {
                    sh "mkdir -p ${TRIVY_CACHE_DIR}"
                    // Solution moderne pour initialiser le cache
                    sh """
                        docker run --rm \
                            -v ${TRIVY_CACHE_DIR}:/root/.cache \
                            aquasec/trivy:latest \
                            trivy --cache-dir /root/.cache image --quiet alpine:latest || \
                            echo "Cache initialisé (le téléchargement se fera automatiquement au premier scan)"
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
                            --quiet \
                            --format table \
                            --security-checks vuln \
                            --exit-code 0 \
                            --severity HIGH,CRITICAL \
                            ${registry}:latest
                    """
                }
            }
        }

        // [Vos autres étapes...]
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
