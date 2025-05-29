pipeline {
    agent any

    environment {
        registry = "omarpfe/projectpfe"              // Nom de l'image Docker
        registryCredential = 'dockerhub'             // Identifiant Jenkins pour Docker Hub
        dockerImage = ''
        SONAR_TOKEN = credentials('jenkins-sonar')   // Token SonarQube
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

        stage('Clean & Build') {
            steps {
                sh 'mvn clean package -Dmaven.test.skip=true'
            }
        }

        stage('Unit Tests') {
            steps {
                sh 'mvn test'
            }
        }

        stage('Analyse SonarQube') {
            steps {
                script {
                    withSonarQubeEnv('sq1') {
                        withEnv(["SONAR_TOKEN=${env.SONAR_TOKEN}"]) {
                            sh 'mvn org.sonarsource.scanner.maven:sonar-maven-plugin:3.9.0.2155:sonar'
                        }
                    }
                }
            }
        }

        stage('Publish to Nexus') {
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

        stage('Trivy Scan') {
            steps {
                script {
                    def cacheDir = '/var/cache/trivy-jenkins'
                    def dbExists = sh(
                        script: "test -d ${cacheDir}/db",
                        returnStatus: true
                    ) == 0

                    if (!dbExists) {
                        error "La base de données Trivy est manquante dans ${cacheDir}. Télécharge-la manuellement."
                    }

                    sh """
                        trivy image \
                          --timeout 10m \
                          --cache-dir ${cacheDir} \
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
                    docker.withRegistry("https://index.docker.io/v1/", registryCredential) {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                script {
                    sh '''
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 "minikube start"
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 "kubectl config use-context minikube"
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 "kubectl apply -f /root/project/docker-spring-boot/deployment.yaml"
                    '''
                }
            }
        }
    }

    post {
        failure {
            echo '❌ Pipeline failed!'
        }
        success {
            echo '✅ Pipeline succeeded!'
        }
    }
}
