pipeline {
    agent any

    environment {
        registry = "omarpfe/projectpfe"
        registryCredential = 'dockerhub'
        dockerImage = ''
        SONAR_TOKEN = credentials('jenkins-sonar')
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

        stage('MVN CLEAN') {
            steps {
                sh "mvn clean"
            }
        }

        stage('ARTIFACT CONSTRUCTION') {
            steps {
                sh 'mvn package -Dmaven.test.skip=true'
            }
        }

        stage('COMPILE') {
            steps {
                sh 'mvn compile'
            }
        }

        stage('UNIT TESTS') {
            steps {
                sh 'mvn test'
            }
        }

        stage('MVN SONARQUBE') {
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

        stage("PUBLISH TO NEXUS") {
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
                    def cacheDir = '/home/jenkins/trivy-cache'
                    def dbFilesExist = sh(
                        script: "test -d ${cacheDir}/db",
                        returnStatus: true
                    ) == 0

                    if (!dbFilesExist) {
                        error "Erreur : La base de données Trivy n'est pas présente dans ${cacheDir}. Veuillez la télécharger manuellement avant de lancer le scan."
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

        stage('Push to Docker Hub') {
            steps {
                script {
                    echo "Début du push Docker..."
                    timeout(time: 3, unit: 'MINUTES') {
                        docker.withRegistry("https://index.docker.io/v1/", registryCredential) {
                            dockerImage.push()
                        }
                    }
                    echo "Push Docker terminé avec succès."
                }
            }
        }
    }

    post {
        failure {
            echo 'Pipeline failed!'
        }
        success {
            echo 'Pipeline succeeded!'
        }
    }
}
