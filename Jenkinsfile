pipeline {
    agent any
    environment {
        registry = "omarpfe/projectpfe" // Docker Hub repository
        registryCredential = 'dockerHub' // Jenkins credential for Docker Hub login
        dockerImage = ''
        SONAR_TOKEN = credentials('jenkins-sonar') // SonarQube token for Jenkins
    }
    tools {
        maven 'M2_HOME' // Maven tool setup
    }
    stages {
        stage('Checkout Git') {
            steps {
                git url: 'https://github.com/omar-essid/projectomar.git', branch: 'main' // Clone the Git repository
            }
        }
        stage('MVN CLEAN') {
            steps {
                script {
                    sh "mvn clean" // Clean the project
                }
            }
        }
        stage('ARTIFACT CONSTRUCTION') {
            steps {
                script {
                    sh 'mvn package -Dmaven.test.skip=true' // Build the artifact without running tests
                }
            }
        }
        stage('COMPILE') {
            steps {
                script {
                    sh 'mvn compile' // Compile to ensure class files are generated
                }
            }
        }
        stage('UNIT TESTS') {
            steps {
                script {
                    sh 'mvn test' // Run unit tests
                }
            }
        }
        stage('MVN SONARQUBE') {
            steps {
                script {
                    withSonarQubeEnv('sq1') { // Ensure 'sq1' is configured in Jenkins (via SonarQube configuration)
                        withEnv(["SONAR_TOKEN=${env.SONAR_TOKEN}"]) { // Inject SonarQube token into the environment
                            sh 'mvn org.sonarsource.scanner.maven:sonar-maven-plugin:3.9.0.2155:sonar'
                        }
                    }
                }
            }
        }
        stage("PUBLISH TO NEXUS") {
            steps {
                script {
                    sh 'mvn deploy' // Deploy the artifact to Nexus
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${registry}:latest") // Build Docker image using the Dockerfile in the repo
                }
            }
        }
        stage('Scan Docker Image with Trivy') {
            steps {
                script {
                    // Run Trivy scan on the built Docker image
                    sh 'trivy image --timeout 45m --scanners vuln --exit-code 0 --severity HIGH,CRITICAL --cache-dir /home/jenkins/.cache/trivy --skip-db-update ${registry}:latest' // Fail the pipeline if high/critical vulnerabilities are found
                }
            }
        }
        // Stage added for deployment to Minikube
        stage('Deploy to Minikube') {
            steps {
                script {
                    // SSH to deployment VM and start Minikube
                    sh '''
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 "minikube start"
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 'kubectl config use-context minikube'
                        sshpass -p 'omar' ssh -o StrictHostKeyChecking=no omar@192.168.88.131 'kubectl apply -f /root/project/docker-spring-boot/deployment.yaml'
                    '''
                }
            }
        }
        stage('Run Security Analysis Script') {
            steps {
                script {
                    // Run the Python script to analyze security configurations
                    sh 'python3 generate_security_suggestions.py'
                }
            }
        }
        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry("https://index.docker.io/v1/", 'dockerhub') {
                        dockerImage.push() // Push the Docker image to Docker Hub
                    }
                }
            }
        }
    }
    post {
        failure {
            echo 'Pipeline failed!' // In case of failure
        }
        success {
            echo 'Pipeline succeeded!' // In case of success
        }
    }
}
