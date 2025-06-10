#!/bin/bash

# === Chemins ===
FULL_LOG="/opt/devsecops-ai/scan-inputs/full_logs.log"
JENKINS_LOG="/var/lib/jenkins/jobs/springboot/builds/9/log"
SONAR_LOG="/var/lib/jenkins/workspace/springboot/target/sonar/report-task.txt"
TRIVY_LOG="/home/jenkins/trivy-cache/logs/trivy.log"
DEPLOYMENT_IP="192.168.88.131"
DEPLOYMENT_USER="omar"
DEPLOYMENT_PASS="omar"

# === Réinitialiser le fichier centralisé ===
echo "🔄 Réinitialisation de $FULL_LOG..."
> "$FULL_LOG"

# === Ajouter les logs Jenkins ===
echo -e "\n===================== 📄 Jenkins Build Log =====================" >> "$FULL_LOG"
if [ -f "$JENKINS_LOG" ]; then
    cat "$JENKINS_LOG" >> "$FULL_LOG"
else
    echo "❌ Jenkins log non trouvé : $JENKINS_LOG" >> "$FULL_LOG"
fi

# === Ajouter les logs SonarQube ===
echo -e "\n===================== 📄 SonarQube Report =====================" >> "$FULL_LOG"
if [ -f "$SONAR_LOG" ]; then
    cat "$SONAR_LOG" >> "$FULL_LOG"
else
    echo "❌ SonarQube report non trouvé : $SONAR_LOG" >> "$FULL_LOG"
fi

# === Ajouter les logs Trivy (optionnel) ===
echo -e "\n===================== 🛡️ Trivy Security Scan =====================" >> "$FULL_LOG"
if [ -f "$TRIVY_LOG" ]; then
    cat "$TRIVY_LOG" >> "$FULL_LOG"
else
    echo "⚠️ Trivy log non trouvé (optionnel) : $TRIVY_LOG" >> "$FULL_LOG"
fi

# === Snapshot Kubernetes via SSH ===
echo -e "\n===================== 📦 Kubernetes Snapshot =====================" >> "$FULL_LOG"
sshpass -p "$DEPLOYMENT_PASS" ssh -o StrictHostKeyChecking=no "$DEPLOYMENT_USER@$DEPLOYMENT_IP" \
    "kubectl get all -o yaml | head -n 50" >> "$FULL_LOG"

echo -e "\n✅ Logs centralisés dans : $FULL_LOG"
# === Mise à jour de la date dans cmdb.json ===
CMDB_JSON="/opt/devsecops-ai/cmdb.json"
if [ -f "$CMDB_JSON" ]; then
    echo "🕒 Mise à jour de la date dans cmdb.json..."
    DATE_NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq --arg date "$DATE_NOW" '.last_updated = $date' "$CMDB_JSON" > /tmp/cmdb_tmp.json && mv /tmp/cmdb_tmp.json "$CMDB_JSON"
else
    echo "⚠️ cmdb.json non trouvé à $CMDB_JSON"
fi
