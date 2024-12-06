pipeline {
    agent any
    environment {
        registry = "omarpfe/projectpfe"
        registryCredential = 'dockerHub'
        dockerImage = ''
        SONAR_TOKEN = credentials('jenkins-sonar') // Utilisation du jeton SonarQube configuré dans Jenkins
    }
    tools {
        maven 'M2_HOME' // Utilisation de l'outil Maven installé sur Jenkins
    }
    stages {
        stage('Checkout Git') {
            steps {
                git url: 'https://github.com/omar-essid/projectomar.git', branch: 'main' // Vérifie l'URL et la branche de ton repository Git
            }
        }
        stage('MVN CLEAN') {
            steps {
                script {
                    sh "mvn clean" // Nettoyage du projet
                }
            }
        }
        stage('ARTIFACT CONSTRUCTION') {
            steps {
                script {
                    sh 'mvn package -Dmaven.test.skip=true' // Construction de l'artifact sans exécuter les tests
                }
            }
        }
        stage('COMPILE') {
            steps {
                script {
                    sh 'mvn compile' // Compilation pour s'assurer que les fichiers de classes sont générés
                }
            }
        }
        stage('UNIT TESTS') {
            steps {
                script {
                    sh 'mvn test' // Exécution des tests unitaires
                }
            }
        }
        stage('MVN SONARQUBE') {
            steps {
                script {
                    withSonarQubeEnv('sq1') {  // Assure-toi que 'sq1' est bien configuré dans Jenkins (via la configuration de SonarQube)
                        withEnv(["SONAR_TOKEN=${env.SONAR_TOKEN}"]) { // Injecte le jeton d'authentification SonarQube dans l'environnement
                            sh 'mvn org.sonarsource.scanner.maven:sonar-maven-plugin:3.9.0.2155:sonar'
                        }
                    }
                }
            }
        }
        stage("PUBLISH TO NEXUS") {
            steps {
                script {
                    sh 'mvn deploy' // Déploiement de l'artifact sur Nexus
                }
            }
        }
    }
    post {
        failure {
            echo 'Pipeline failed!' // Message en cas d'échec de la pipeline
        }
        success {
            echo 'Pipeline succeeded!' // Message en cas de réussite de la pipeline
        }
    }
}
