# Étape 1 : Builder (optionnel si déjà fait côté Jenkins)
# Si ton WAR est déjà construit par Jenkins, tu peux ignorer cette étape et rester avec une seule image finale.

# Étape 2 : Image minimale pour exécution
FROM eclipse-temurin:17-jre-alpine

# Répertoire de travail (facultatif mais propre)
WORKDIR /app

# Copier uniquement le WAR (meilleure couche de cache si le fichier change rarement)
COPY target/docker-spring-boot.war app.war

# Exposer le port utilisé par ton application
EXPOSE 8083

# Lancer l'application
ENTRYPOINT ["java", "-jar", "app.war"]
