from transformers import GPT2LMHeadModel, GPT2Tokenizer, DistilBertForSequenceClassification, DistilBertTokenizer
import torch
import logging
import warnings
import os

# Désactiver les avertissements
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)

# Charger le modèle GPT-2 pour la génération de texte
gpt2_model = GPT2LMHeadModel.from_pretrained('gpt2')
gpt2_tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

# Charger le modèle DistilBERT pour la classification de texte
distilbert_model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased')
distilbert_tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

def generate_suggestions(file_content):
    """
    Génère des suggestions de sécurité à partir du contenu du fichier
    en utilisant GPT-2 pour la génération de texte.
    """
    # Encoder le texte du fichier avec GPT-2
    inputs = gpt2_tokenizer.encode(file_content, return_tensors='pt')

    # Générer du texte avec GPT-2
    outputs = gpt2_model.generate(
        inputs,
        max_new_tokens=200,
        num_return_sequences=1,
        no_repeat_ngram_size=2,
        temperature=0.7,
        do_sample=True,
        top_k=50,
        top_p=0.95
    )

    # Décoder la sortie générée
    generated_text = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Filtrer les sections YAML pertinentes
    filtered_text = "\n".join(line for line in generated_text.splitlines() if ":" in line or line.strip() == "---")
    
    return filtered_text

def classify_security_risks(text):
    """
    Classe les risques de sécurité du texte en utilisant DistilBERT pour la classification.
    Retourne également les sections à risque détectées.
    """
    inputs = distilbert_tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = distilbert_model(**inputs)
    
    # Récupérer les scores de classification
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=-1).item()

    # Ajouter une analyse basique des risques
    risky_sections = []
    if "NodePort" in text:
        risky_sections.append("L'utilisation de 'NodePort' peut exposer des ports inutiles à Internet.")
    if "latest" in text:
        risky_sections.append("L'utilisation de l'image 'latest' peut entraîner des problèmes de versionnement.")
    
    # Retourner un état détaillé
    if predictions == 1:
        return f"⚠️ Risque élevé détecté!\nDétails :\n" + "\n".join(risky_sections)
    else:
        return "✅ Configuration sécurisée."

# Définir le chemin du fichier deployment.yaml
use_local_path = False  # Modifiez cette variable selon l'environnement
if use_local_path:
    file_path = '/mnt/deployment_root/project/docker-spring-boot/deployment.yaml'
else:
    file_path = 'deployment.yaml'  # Depuis le repository Git

# Charger le fichier deployment.yaml
if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        file_content = f.read()

    # Générer des suggestions de sécurité
    generated_suggestions = generate_suggestions(file_content)

    # Classifier les risques de sécurité
    security_status = classify_security_risks(file_content)

    # Afficher les suggestions générées avec un format amélioré
    print("Suggestions générées avec formatage :")
    print(generated_suggestions)

    # Afficher l'état de sécurité
    print("\nÉtat de sécurité :")
    print(security_status)
else:
    print(f"⚠️ Le fichier '{file_path}' est introuvable. Vérifiez le chemin spécifié.")
