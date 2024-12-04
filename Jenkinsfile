pipeline {
    agent any
    environment {
        registry = "omarpfe/projectpfe"
        registryCredential = 'dockerHub'
        dockerImage = ''
    }
    tools {
        maven 'M2_HOME'
    }
    stages {
        stage('Checkout Git') {
            steps {
                git url: 'https://github.com/omar-essid/projectomar.git', branch: 'main'
            }
        }
        stage('MVN CLEAN') {
            steps {
                script {
                    sh "mvn clean"
                }
            }
        }
        stage('ARTIFACT CONSTRUCTION') {
            steps {
                script {
                    sh 'mvn package -Dmaven.test.skip=true -P test-coverage'
                }
            }
        }
        stage('UNIT TESTS') {
            steps {
                script {
                    sh 'mvn test'
                }
            }
        }
        stage('MVN SONARQUBE') {
            steps {
                script {
                    withSonarQubeEnv('sq1') {  // 'sq1' doit correspondre au nom de l'installation SonarQube dans Jenkins
                        sh './mvnw clean org.sonarsource.scanner.maven:sonar-maven-plugin:3.9.0.2155:sonar'
                    }
                }
            }
        }
        stage("PUBLISH TO NEXUS") {
            steps {
                script {
                    sh 'mvn deploy'
                }
            }
        }
    }
    post {
        failure {
            echo 'Pipeline failed!'
        }
    }
}
