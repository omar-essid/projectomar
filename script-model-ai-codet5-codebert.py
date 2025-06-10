#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import torch
import textwrap
from tabulate import tabulate
from termcolor import colored
from transformers import RobertaTokenizer, RobertaForSequenceClassification, AutoTokenizer, T5ForConditionalGeneration

# Chemins des fichiers
CMDB_PATH = "/opt/devsecops-ai/cmdb.json"
CODEBERT_PATH = "/opt/devsecops-ai/model-ai/models/codebert-base"
CODET5_PATH = "/opt/devsecops-ai/model-ai/models/codet5-small"
LOG_PATH = "/opt/devsecops-ai/scan-inputs/full_logs.log"

# Configuration
MAX_LINE_WIDTH = 80
SEPARATOR = "═" * MAX_LINE_WIDTH
SUBSEPARATOR = "─" * MAX_LINE_WIDTH

# Couleurs et icônes
ICONS = {
    "error": "❌", "warning": "⚠️", "success": "✅",
    "info": "ℹ️", "critical": "🔥", "suggestion": "💡",
    "search": "🔍", "jenkins": "⚙️", "sonarqube": "🛡️",
    "trivy": "🔎", "kubernetes": "☸️", "springboot": "🌱"
}

COLORS = {
    "high": "red", "medium": "yellow", "low": "green",
    "header": "cyan", "title": "magenta", "normal": "white",
    "code": "grey", "highlight": "yellow"
}

def print_header(title, icon="ℹ️"):
    print(colored(f"\n{SEPARATOR}", COLORS["header"]))
    print(colored(f"{icon} {title}".center(MAX_LINE_WIDTH), COLORS["header"], attrs=["bold"]))
    print(colored(SEPARATOR, COLORS["header"]))

def print_subheader(title):
    print(colored(f"\n{title}", COLORS["title"], attrs=["bold"]))
    print(colored(SUBSEPARATOR, COLORS["title"]))

def get_severity(score):
    if score > 75: return "high", "🔴 Critique"
    elif score > 50: return "medium", "🟠 Moyenne"
    else: return "low", "🟢 Faible"

def format_code_block(text, max_lines=8):
    lines = text.split('\n')
    if len(lines) > max_lines:
        return '\n'.join(lines[:max_lines]) + '\n[...]'
    return text

def load_cmdb():
    if not os.path.isfile(CMDB_PATH):
        print(colored(f"{ICONS['error']} Fichier CMDB introuvable: {CMDB_PATH}", COLORS["high"]))
        return {}
    with open(CMDB_PATH, "r") as f:
        return json.load(f)

def analyze_logs():
    print_header("🔍 ANALYSE APPROFONDIE DES LOGS", ICONS["search"])
    
    # Chargement des modèles
    print(colored("\n🔧 Chargement des modèles d'IA...", COLORS["normal"]))
    try:
        codebert_tokenizer = RobertaTokenizer.from_pretrained(CODEBERT_PATH)
        codebert_model = RobertaForSequenceClassification.from_pretrained(CODEBERT_PATH)
        codet5_tokenizer = AutoTokenizer.from_pretrained(CODET5_PATH)
        codet5_model = T5ForConditionalGeneration.from_pretrained(CODET5_PATH)
    except Exception as e:
        print(colored(f"{ICONS['error']} Erreur lors du chargement des modèles: {str(e)}", COLORS["high"]))
        return []

    if not os.path.isfile(LOG_PATH):
        print(colored(f"{ICONS['error']} Fichier introuvable: {LOG_PATH}", COLORS["high"]))
        return []

    with open(LOG_PATH, "r") as f:
        logs = f.read()

    results = []
    log_segments = logs.split("\n\n")

    for segment in log_segments:
        if not segment.strip(): continue

        try:
            service, problem_type, critical_issue = detect_issues(segment)
            
            # Analyse avec CodeBERT
            inputs = codebert_tokenizer(segment, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = codebert_model(**inputs)
            score = round(torch.softmax(outputs.logits, dim=1)[0][1].item() * 100, 2)

            # Génération de suggestion améliorée
            suggestion = generate_custom_suggestion(service, problem_type, critical_issue, segment)
            
            results.append({
                "service": service,
                "type": problem_type,
                "score": score,
                "segment": segment.strip(),
                "suggestion": suggestion,
                "critical_issue": critical_issue
            })
            
        except Exception as e:
            print(colored(f"{ICONS['warning']} Erreur analyse segment: {str(e)}", COLORS["medium"]))
            continue

    return results

def detect_issues(log_segment):
    # Détection des problèmes spécifiques
    service = "Autre"
    problem_type = "Information"
    critical_issue = None
    
    # Détection Jenkins
    if "Started by user" in log_segment or "Jenkins Build Log" in log_segment:
        service = "Jenkins"
        if "Selected Git installation does not exist" in log_segment:
            problem_type = "Erreur Git"
            critical_issue = "Configuration Git manquante"
        elif "No credentials specified" in log_segment:
            problem_type = "Problème d'authentification"
            critical_issue = "Identifiants Git non configurés"
        else:
            problem_type = "Exécution de build"
    
    # Détection SonarQube
    elif "SonarQube Report" in log_segment or "sonar-maven-plugin" in log_segment:
        service = "SonarQube"
        if "SonarQube server can not be reached" in log_segment:
            problem_type = "Erreur connexion"
            critical_issue = "Serveur SonarQube inaccessible"
        else:
            problem_type = "Analyse de code"
    
    # Détection Trivy
    elif "Trivy Security Scan" in log_segment:
        service = "Trivy"
        if "log non trouvé" in log_segment:
            problem_type = "Problème de configuration"
            critical_issue = "Fichier de logs Trivy manquant"
        else:
            problem_type = "Scan de sécurité"
    
    # Détection Kubernetes
    elif "apiVersion: v1" in log_segment:
        service = "Kubernetes"
        problem_type = "Configuration"
    
    # Détection Spring Boot
    elif "Started DockerSpringBootApplicationTests" in log_segment:
        service = "SpringBoot"
        problem_type = "Exécution de tests"
    
    return service, problem_type, critical_issue

def generate_custom_suggestion(service, problem_type, critical_issue, context):
    # Suggestions pré-définies basées sur les problèmes détectés
    suggestions = {
        # Jenkins
        "Configuration Git manquante": "Configurer correctement Git dans Jenkins :\n1. Allez dans 'Manage Jenkins' > 'Global Tool Configuration'\n2. Ajoutez une installation Git valide\n3. Spécifiez le chemin vers l'exécutable git",
        "Identifiants Git non configurés": "Ajouter des identifiants Git dans Jenkins :\n1. Créez une entrée dans 'Credentials'\n2. Utilisez des tokens d'accès personnels au lieu de mots de passe\n3. Vérifiez les permissions du repository",
        
        # SonarQube
        "Serveur SonarQube inaccessible": """Résoudre les problèmes de connexion à SonarQube :
1. Vérifiez que le serveur SonarQube est en cours d'exécution (http://192.168.88.130:9000)
2. Vérifiez les paramètres réseau/firewall
3. Mettez à jour la configuration dans pom.xml ou les paramètres Jenkins""",
        
        # Trivy
        "Fichier de logs Trivy manquant": """Configurer Trivy correctement :
1. Créez le répertoire /home/jenkins/trivy-cache/logs/
2. Assurez-vous que Jenkins a les permissions d'écriture
3. Configurez Trivy pour générer des logs détaillés""",
        
        # Kubernetes
        "Configuration": """Meilleures pratiques Kubernetes :
1. Ajoutez des resource limits aux conteneurs
2. Configurez des liveness/readiness probes
3. Utilisez des secrets pour les données sensibles""",
    }
    
    # Si on a détecté un problème critique, utiliser la suggestion pré-définie
    if critical_issue and critical_issue in suggestions:
        return suggestions[critical_issue]
    
    # Sinon, générer une suggestion avec CodeT5
    prompt = f"Problème dans {service} ({problem_type}). Contexte: {context[:300]}\nRecommandation:"
    try:
        inputs = codet5_tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        outputs = codet5_model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=150,
            num_beams=4,
            early_stopping=True
        )
        return codet5_tokenizer.decode(outputs[0], skip_special_tokens=True)
    except:
        return "Impossible de générer une recommandation pour ce problème."

def print_log_analysis_details(results):
    print_header("📝 DIAGNOSTIC DÉTAILLÉ PAR SERVICE", ICONS["info"])
    
    for idx, result in enumerate(results, 1):
        severity_level, severity_text = get_severity(result["score"])
        service_icon = ICONS.get(result["service"].lower(), ICONS["info"])
        
        print_subheader(f"{service_icon} Service #{idx}: {result['service']} - {result['type']}")
        
        if result["critical_issue"]:
            print(colored("🚨 Problème critique:", COLORS["high"]), colored(result["critical_issue"], COLORS["high"]))
        
        print(colored("\n📊 Score de risque:", COLORS["title"]), colored(f"{result['score']}%", COLORS[severity_level]))
        print(colored("📌 Niveau de sévérité:", COLORS["title"]), colored(severity_text, COLORS[severity_level]))
        
        print(colored("\n🔍 Extrait du log:", COLORS["title"]))
        print(colored(format_code_block(result["segment"]), COLORS["code"]))
        
        print(colored("\n💡 Recommandation:", COLORS["title"]))
        print(colored(textwrap.fill(result["suggestion"], width=MAX_LINE_WIDTH), COLORS["highlight"]))
        
        print("\n" + "─" * (MAX_LINE_WIDTH // 2))

def analyze_cmdb_configurations(cmdb_data):
    print_header("🛠️ AUDIT DES CONFIGURATIONS CMDB", ICONS["info"])
    
    if not cmdb_data:
        print(colored(f"{ICONS['warning']} Aucune donnée CMDB à analyser", COLORS["medium"]))
        return []

    results = []
    
    for env, services in cmdb_data.get("environments", {}).items():
        print_subheader(f"Environnement: {env}")
        
        for service, config in services.items():
            # Analyse spécifique pour chaque service
            analysis_result = analyze_service_config(service, config, env)
            results.append(analysis_result)
            
            # Affichage des détails
            service_icon = ICONS.get(service.lower(), ICONS["info"])
            print(colored(f"\n{service_icon} Service: {service}", COLORS["title"]))
            print(colored(f"📌 Version: {config.get('version', 'N/A')}", COLORS["normal"]))
            
            if analysis_result["issues"]:
                print(colored("🚨 Problèmes identifiés:", COLORS["high"]))
                for issue in analysis_result["issues"]:
                    print(f"- {issue}")
            
            print(colored("\n💡 Recommandation:", COLORS["title"]))
            print(colored(textwrap.fill(analysis_result["suggestion"], width=MAX_LINE_WIDTH), COLORS["highlight"]))
    
    return results

def analyze_service_config(service, config, env):
    issues = []
    suggestion = ""
    base_score = 30
    
    # Règles d'analyse spécifiques
    if service == "jenkins":
        if config.get("version", "") < "2.414":
            issues.append("Version de Jenkins obsolète (vulnérabilités de sécurité)")
            base_score += 30
        suggestion = """Recommandations Jenkins:
1. Mettre à jour vers la dernière version LTS
2. Configurer le plugin des credentials Git
3. Activer le monitoring des jobs"""
    
    elif service == "sonarqube":
        if config.get("version", "").startswith("9.9"):
            issues.append("Version 9.9.4 n'est plus supportée")
            base_score += 40
        suggestion = """Recommandations SonarQube:
1. Mettre à jour vers la version 10.x LTS
2. Configurer des règles qualité personnalisées
3. Planifier des analyses régulières"""
    
    elif service == "trivy":
        if config.get("version", "") < "0.50":
            issues.append("Version de Trivy trop ancienne")
            base_score += 20
        if not os.path.exists(config.get("logs", "")):
            issues.append("Chemin des logs incorrect")
            base_score += 20
        suggestion = """Recommandations Trivy:
1. Mettre à jour vers la dernière version
2. Configurer des scans planifiés
3. Stocker les résultats dans une base de données"""
    
    elif service == "minikube":
        if config.get("version", "") < "v1.30":
            issues.append("Version de Minikube obsolète")
            base_score += 30
        suggestion = """Recommandations Minikube:
1. Mettre à jour vers v1.33+
2. Configurer des ressources dédiées
3. Activer les monitoring addons"""
    
    elif service == "springboot-app":
        if not config.get("resources", ""):
            issues.append("Limites de ressources non configurées")
            base_score += 40
        suggestion = """Recommandations SpringBoot:
1. Configurer des resource limits
2. Ajouter des health checks
3. Configurer le scaling automatique"""
    
    # Calcul du score final (max 100)
    score = min(base_score + len(config)*5, 100)
    
    return {
        "service": service,
        "environment": env,
        "version": config.get("version", "N/A"),
        "score": score,
        "issues": issues,
        "suggestion": suggestion
    }

def print_summary_table(results, title, context):
    print_header(f"📊 SYNTHÈSE - {title}", ICONS["info"])
    
    table_data = []
    for idx, r in enumerate(results, 1):
        sev_level, sev_text = get_severity(r["score"])
        
        # Formatage différent pour les logs et le CMDB
        if context == "logs":
            description = r["type"]
            if r["critical_issue"]:
                description += f" ({r['critical_issue']})"
            suggestion = textwrap.shorten(r["suggestion"], width=60, placeholder="...")
        else:
            description = r["environment"]
            suggestion = textwrap.shorten(r["suggestion"], width=60, placeholder="...")
        
        table_data.append([
            idx,
            r["service"],
            description,
            colored(sev_text, COLORS[sev_level]),
            f"{r['score']}%",
            suggestion
        ])
    
    headers = ["ID", "Service", "Description", "Sévérité", "Score", "Recommandation"]
    print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[None, 15, 15, 10, 8, 40]))

def main():
    # Analyse des logs
    log_results = analyze_logs()
    if log_results:
        print_log_analysis_details(log_results)
        print_summary_table(log_results, "ANALYSE DES LOGS", "logs")
    
    # Analyse du CMDB
    cmdb_data = load_cmdb()
    cmdb_results = analyze_cmdb_configurations(cmdb_data)
    if cmdb_results:
        print_summary_table(cmdb_results, "AUDIT CMDB", "cmdb")

if __name__ == "__main__":
    main()
