#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import torch
import textwrap
from datetime import datetime
from tabulate import tabulate
from termcolor import colored
from transformers import RobertaTokenizer, RobertaForSequenceClassification, AutoTokenizer, T5ForConditionalGeneration

# Chemins des fichiers
CMDB_PATH = "/opt/devsecops-ai/cmdb.json"
CODEBERT_PATH = "/opt/devsecops-ai/model-ai/models/codebert-base"
CODET5_PATH = "/opt/devsecops-ai/model-ai/models/codet5-small"
LOG_PATH = "/opt/devsecops-ai/scan-inputs/full_logs.log"
OUTPUT_TXT_PATH = "/opt/devsecops-ai/cmdb-ai.txt"

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

def save_output_to_file(content):
    """Sauvegarde le contenu dans le fichier de sortie avec timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        separator = "\n" + "="*80 + "\n"
        
        with open(OUTPUT_TXT_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n{separator}ANALYSE DU {timestamp}{separator}\n")
            # Enlever les codes de couleur pour le fichier texte
            clean_content = re.sub(r'\x1b\[[0-9;]*m', '', content)
            f.write(clean_content + "\n")
        
        print(colored(f"\n{ICONS['success']} Résultats sauvegardés dans {OUTPUT_TXT_PATH}", "green"))
    except Exception as e:
        print(colored(f"{ICONS['error']} Erreur lors de la sauvegarde: {str(e)}", "red"))

def print_header(title, icon="ℹ️"):
    header = f"\n{SEPARATOR}\n{icon} {title}".center(MAX_LINE_WIDTH) + f"\n{SEPARATOR}"
    print(colored(header, COLORS["header"], attrs=["bold"]))
    return header + "\n"

def print_subheader(title):
    subheader = f"\n{title}\n{SUBSEPARATOR}"
    print(colored(subheader, COLORS["title"], attrs=["bold"]))
    return subheader + "\n"

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
    try:
        with open(CMDB_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(colored(f"{ICONS['error']} Fichier CMDB corrompu", COLORS["high"]))
        return {}

def detect_issues(log_segment):
    service = "Autre"
    problem_type = "Information"
    critical_issue = None
    
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
    
    elif "SonarQube Report" in log_segment or "sonar-maven-plugin" in log_segment:
        service = "SonarQube"
        if "SonarQube server can not be reached" in log_segment:
            problem_type = "Erreur connexion"
            critical_issue = "Serveur SonarQube inaccessible"
        else:
            problem_type = "Analyse de code"
    
    elif "Trivy Security Scan" in log_segment:
        service = "Trivy"
        if "log non trouvé" in log_segment:
            problem_type = "Problème de configuration"
            critical_issue = "Fichier de logs Trivy manquant"
        else:
            problem_type = "Scan de sécurité"
    
    elif "apiVersion: v1" in log_segment:
        service = "Kubernetes"
        problem_type = "Configuration"
    
    elif "Started DockerSpringBootApplicationTests" in log_segment:
        service = "SpringBoot"
        problem_type = "Exécution de tests"
    
    return service, problem_type, critical_issue

def generate_custom_suggestion(service, problem_type, critical_issue, context):
    suggestions = {
        "Configuration Git manquante": "Configurer correctement Git dans Jenkins :\n1. Allez dans 'Manage Jenkins' > 'Global Tool Configuration'\n2. Ajoutez une installation Git valide\n3. Spécifiez le chemin vers l'exécutable git",
        "Identifiants Git non configurés": "Ajouter des identifiants Git dans Jenkins :\n1. Créez une entrée dans 'Credentials'\n2. Utilisez des tokens d'accès personnels\n3. Vérifiez les permissions du repository",
        "Serveur SonarQube inaccessible": "Résoudre les problèmes de connexion :\n1. Vérifiez que le serveur SonarQube est en cours d'exécution\n2. Vérifiez les paramètres réseau/firewall\n3. Mettez à jour la configuration",
        "Fichier de logs Trivy manquant": "Configurer Trivy :\n1. Créez le répertoire /home/jenkins/trivy-cache/logs/\n2. Assurez-vous que Jenkins a les permissions d'écriture",
        "Configuration": "Meilleures pratiques Kubernetes :\n1. Ajoutez des resource limits\n2. Configurez des liveness/readiness probes\n3. Utilisez des secrets"
    }
    
    if critical_issue and critical_issue in suggestions:
        return suggestions[critical_issue]
    
    try:
        prompt = f"Problème dans {service} ({problem_type}). Contexte: {context[:300]}\nRecommandation:"
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

def analyze_logs():
    output_content = print_header("🔍 ANALYSE APPROFONDIE DES LOGS", ICONS["search"])
    
    # Chargement des modèles
    output_content += "\n🔧 Chargement des modèles d'IA...\n"
    print(colored("\n🔧 Chargement des modèles d'IA...", COLORS["normal"]))
    try:
        codebert_tokenizer = RobertaTokenizer.from_pretrained(CODEBERT_PATH)
        codebert_model = RobertaForSequenceClassification.from_pretrained(CODEBERT_PATH)
        codet5_tokenizer = AutoTokenizer.from_pretrained(CODET5_PATH)
        codet5_model = T5ForConditionalGeneration.from_pretrained(CODET5_PATH)
    except Exception as e:
        error_msg = f"{ICONS['error']} Erreur lors du chargement des modèles: {str(e)}"
        output_content += error_msg + "\n"
        print(colored(error_msg, COLORS["high"]))
        return [], output_content

    if not os.path.isfile(LOG_PATH):
        error_msg = f"{ICONS['error']} Fichier introuvable: {LOG_PATH}"
        output_content += error_msg + "\n"
        print(colored(error_msg, COLORS["high"]))
        return [], output_content

    with open(LOG_PATH, "r") as f:
        logs = f.read()

    results = []
    log_segments = logs.split("\n\n")

    for segment in log_segments:
        if not segment.strip(): continue

        try:
            service, problem_type, critical_issue = detect_issues(segment)
            
            inputs = codebert_tokenizer(segment, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = codebert_model(**inputs)
            score = round(torch.softmax(outputs.logits, dim=1)[0][1].item() * 100, 2)

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
            error_msg = f"{ICONS['warning']} Erreur analyse segment: {str(e)}"
            output_content += error_msg + "\n"
            print(colored(error_msg, COLORS["medium"]))
            continue

    return results, output_content

def print_log_analysis_details(results):
    output_content = print_header("📝 DIAGNOSTIC DÉTAILLÉ PAR SERVICE", ICONS["info"])
    
    for idx, result in enumerate(results, 1):
        severity_level, severity_text = get_severity(result["score"])
        service_icon = ICONS.get(result["service"].lower(), ICONS["info"])
        
        output_content += print_subheader(f"{service_icon} Service #{idx}: {result['service']} - {result['type']}")
        
        if result["critical_issue"]:
            crit_msg = f"🚨 Problème critique: {result['critical_issue']}"
            output_content += crit_msg + "\n"
            print(colored(crit_msg, COLORS["high"]))
        
        score_msg = f"📊 Score de risque: {result['score']}%"
        sev_msg = f"📌 Niveau de sévérité: {severity_text}"
        output_content += "\n" + score_msg + "\n"
        output_content += sev_msg + "\n"
        print(colored("\n" + score_msg, COLORS["title"]))
        print(colored(sev_msg, COLORS["title"]))
        
        output_content += "\n🔍 Extrait du log:\n"
        output_content += format_code_block(result["segment"]) + "\n"
        print(colored("\n🔍 Extrait du log:", COLORS["title"]))
        print(colored(format_code_block(result["segment"]), COLORS["code"]))
        
        output_content += "\n💡 Recommandation:\n"
        output_content += textwrap.fill(result["suggestion"], width=MAX_LINE_WIDTH) + "\n"
        print(colored("\n💡 Recommandation:", COLORS["title"]))
        print(colored(textwrap.fill(result["suggestion"], width=MAX_LINE_WIDTH), COLORS["highlight"]))
        
        output_content += "\n" + "─" * (MAX_LINE_WIDTH // 2) + "\n"
        print("\n" + "─" * (MAX_LINE_WIDTH // 2))
    
    return output_content

def analyze_service_config(service, config, env):
    issues = []
    suggestion = ""
    base_score = 30
    
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
    
    score = min(base_score + len(config)*5, 100)
    
    return {
        "service": service,
        "environment": env,
        "version": config.get("version", "N/A"),
        "score": score,
        "issues": issues,
        "suggestion": suggestion
    }

def analyze_cmdb_configurations(cmdb_data):
    output_content = print_header("🛠️ AUDIT DES CONFIGURATIONS CMDB", ICONS["info"])
    
    if not cmdb_data:
        msg = f"{ICONS['warning']} Aucune donnée CMDB à analyser"
        output_content += msg + "\n"
        print(colored(msg, COLORS["medium"]))
        return [], output_content

    results = []
    
    for env, services in cmdb_data.get("environments", {}).items():
        output_content += print_subheader(f"Environnement: {env}")
        
        for service, config in services.items():
            analysis_result = analyze_service_config(service, config, env)
            results.append(analysis_result)
            
            service_icon = ICONS.get(service.lower(), ICONS["info"])
            output_content += f"\n{service_icon} Service: {service}\n"
            output_content += f"📌 Version: {config.get('version', 'N/A')}\n"
            print(colored(f"\n{service_icon} Service: {service}", COLORS["title"]))
            print(colored(f"📌 Version: {config.get('version', 'N/A')}", COLORS["normal"]))
            
            if analysis_result["issues"]:
                output_content += "🚨 Problèmes identifiés:\n"
                print(colored("🚨 Problèmes identifiés:", COLORS["high"]))
                for issue in analysis_result["issues"]:
                    output_content += f"- {issue}\n"
                    print(f"- {issue}")
            
            output_content += "\n💡 Recommandation:\n"
            output_content += textwrap.fill(analysis_result["suggestion"], width=MAX_LINE_WIDTH) + "\n"
            print(colored("\n💡 Recommandation:", COLORS["title"]))
            print(colored(textwrap.fill(analysis_result["suggestion"], width=MAX_LINE_WIDTH), COLORS["highlight"]))
    
    return results, output_content

def print_summary_table(results, title, context):
    output_content = print_header(f"📊 SYNTHÈSE - {title}", ICONS["info"])
    
    table_data = []
    for idx, r in enumerate(results, 1):
        sev_level, sev_text = get_severity(r["score"])
        
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
            sev_text,
            f"{r['score']}%",
            suggestion
        ])
    
    headers = ["ID", "Service", "Description", "Sévérité", "Score", "Recommandation"]
    table = tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[None, 15, 15, 10, 8, 40])
    
    output_content += table + "\n"
    print(table)
    
    return output_content

def main():
    full_output = ""
    
    # Analyse des logs
    log_results, log_output = analyze_logs()
    full_output += log_output
    if log_results:
        full_output += print_log_analysis_details(log_results)
        full_output += print_summary_table(log_results, "ANALYSE DES LOGS", "logs")
    
    # Analyse du CMDB
    cmdb_data = load_cmdb()
    cmdb_results, cmdb_output = analyze_cmdb_configurations(cmdb_data)
    full_output += cmdb_output
    if cmdb_results:
        full_output += print_summary_table(cmdb_results, "AUDIT CMDB", "cmdb")
    
    # Sauvegarde des résultats
    save_output_to_file(full_output)

if __name__ == "__main__":
    main()
