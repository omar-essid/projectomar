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
                    sh 'mvn sonar:sonar -Dsonar.login=admin -Dsonar.password=Om07410681ar?'
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
