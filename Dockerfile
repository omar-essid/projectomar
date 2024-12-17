# Utiliser l'image de base Java 17
FROM openjdk:17-jdk-slim

# Exposer le port 8083
EXPOSE 8083

# Ajouter le fichier WAR compilé dans l'image
ADD target/docker-spring-boot.war docker-spring-boot.war

# Définir le point d'entrée pour démarrer l'application
ENTRYPOINT ["java", "-jar", "/docker-spring-boot.war"]

