import json
import spacy
import warnings
from skillNer.skill_extractor_class import SkillExtractor
from spacy.matcher import PhraseMatcher
import numpy as np

# Désactiver les warnings de word vectors
warnings.filterwarnings("ignore", category=UserWarning, module="skillNer.utils")

# ==========================================================
# Charger ton JSON et extraire toutes les surface forms
# ==========================================================
def extract_from_extractor(extractor, text, tresh=0.5):
    # `extractor.annotate` expects a raw string. Ensure we pass a string.
    res = extractor.annotate(text, tresh=tresh)

    skills = []
    
    # Handle full_matches safely
    for m in res['results'].get('full_matches', []):
        skill_id = m.get('skill_id')
        if skill_id and skill_id in extractor.skills_db:
            skills.append({
                "skill_id": skill_id,
                "skill_name": extractor.skills_db[skill_id]['skill_name'],
                "type": "full",
            })
    
    # Handle ngram_scored safely
    for m in res['results'].get('ngram_scored', []):
        skill_id = m.get('skill_id')
        if skill_id and skill_id in extractor.skills_db:
            skills.append({
                "skill_id": skill_id,
                "skill_name": extractor.skills_db[skill_id]['skill_name'],
                "type": "ngram",
                "score": m.get("score", 1),
            })

    # Return a flat structure: text and list of detected skills
    return {"text": res.get('text', text), "results": skills}

def load_skill_terms(json_path="skill_db_relax_20.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # SkillNER attend : data[skill_key]["skill_len"]
    for key, info in data.items():
        if "skill_name" in info:
            name = info["skill_name"]
        else:
            continue  # skill incomplet → on ignore

        # Calcul automatique de la longueur du skill (nb de mots)
        info["skill_len"] = len(name.split())

    return data

# ==========================================================
# Créer le SkillExtractor
# ==========================================================
def create_extractor(skill_terms):
    # Charger spaCy sans les composants inutiles pour plus de vitesse
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    
    # Charger les token distances si disponibles
    try:
        with open("token_dist.json", "r", encoding="utf-8") as f:
            token_dist = json.load(f)
        
        # Créer des vecteurs simples basés sur la fréquence relative
        if token_dist:
            max_freq = max(token_dist.values()) if token_dist else 1
            for token_str, freq in token_dist.items():
                if token_str in nlp.vocab:
                    # Utiliser la fréquence pour injecter une information dans le vecteur
                    normalized_freq = freq / max_freq if max_freq > 0 else 0.5
                    nlp.vocab.set_vector(token_str, np.random.rand(96) * normalized_freq)
    except FileNotFoundError:
        pass  # token_dist.json non trouvé, continuer sans
    except Exception as e:
        print(f"Info: Could not load token_dist.json: {e}")
    
    # Pass the PhraseMatcher class (SkillExtractor will instantiate it
    # internally with the expected args: e.g. PhraseMatcher(nlp.vocab, attr="LOWER"))
    return SkillExtractor(nlp, skills_db=skill_terms, phraseMatcher=PhraseMatcher)


# ==========================================================
# Fonction d’extraction
# ==========================================================
def extract_skills(text, extractor):
    # The extractor expects a raw string, not a spaCy Doc
    results = extract_from_extractor(extractor, text)

    found = []
    for r in results["results"]:
        found.append(r["skill_name"])

    return list(dict.fromkeys(found))


# ==========================================================
# Exemple d’utilisation
# ==========================================================
if __name__ == "__main__":
    print("📌 Chargement des skills...")
    skill_terms = load_skill_terms("skill_db_relax_20.json")

    print(f"🔧 {len(skill_terms)} termes chargés.")

    extractor = create_extractor(skill_terms)
    texte = """
            "description": "Objectifs de la mission\n\nLe Data Modeler interviendra au sein du d\u00e9partement Marketing & Sales d\u2019ENGIE pour concevoir, structurer et maintenir les mod\u00e8les de donn\u00e9es n\u00e9cessaires \u00e0 la bonne exploitation des informations clients, ventes et marketing.\nL\u2019objectif principal est de garantir la qualit\u00e9, la coh\u00e9rence et la disponibilit\u00e9 des donn\u00e9es utilis\u00e9es par les \u00e9quipes business et data (analystes, data engineers, data scientists) afin de soutenir la strat\u00e9gie data-driven du groupe.\n\nEnvironnement / Contexte\n\nP\u00e9rim\u00e8tre : marketing, ventes et exp\u00e9rience client\n\nEnvironnement collaboratif : \u00e9quipe mixte Data Engineers / BI / business analysts\n\nContexte international avec interactions r\u00e9guli\u00e8res avec les \u00e9quipes centrales\n\nPr\u00e9sence sur site \u00e0 Bruxelles 2 jours par semaine, le reste en remote\n\nM\u00e9thodologie de travail agile (scrum ou kanban selon les \u00e9quipes)\n\n\n\nDur\u00e9e / Dispo / Lieu\n\nDur\u00e9e : mission longue (initiale 12 mois renouvelable)\n\nDisponibilit\u00e9 : d\u00e8s que possible\n\nLieu : Bruxelles, 2 jours sur site / 3 jours t\u00e9l\u00e9travail\n\nLangues / TJM cible\n\nFran\u00e7ais ou anglais professionnel obligatoire (environnement bilingue)\n\nTJM maximum : 600 \u20ac / jour",
            "criteria": "Stack technique / outils\n\nMod\u00e9lisation de donn\u00e9es : Data Vault, Kimball, Inmon, ou \u00e9quivalents\n\nBases de donn\u00e9es : Snowflake, BigQuery, ou SQL Server\n\nLangage de requ\u00eate : SQL avanc\u00e9 (optimisation de requ\u00eates, vues mat\u00e9rialis\u00e9es, contraintes d\u2019int\u00e9grit\u00e9)\n\nOutils de data pipeline / ETL : dbt, Informatica, Talend, ou Azure Data Factory\n\nEnvironnement cloud : Azure (pr\u00e9f\u00e9r\u00e9) ou GCP\n\nDocumentation & data catalog : Collibra, Dataedo, Confluence\n\nComp\u00e9tences attendues\n\nMa\u00eetrise des principes de mod\u00e9lisation relationnelle et dimensionnelle\n\nCapacit\u00e9 \u00e0 traduire les besoins m\u00e9tiers en mod\u00e8les de donn\u00e9es robustes et \u00e9volutifs\n\nConnaissance des standards de gouvernance et de qualit\u00e9 des donn\u00e9es\n\nAptitude \u00e0 collaborer avec les \u00e9quipes m\u00e9tiers et techniques pour assurer la coh\u00e9rence du mod\u00e8le global\n\nExp\u00e9rience dans un contexte data warehouse / marketing data platform\n\nExp\u00e9rience minimum : 4 \u00e0 5 ans sur un poste de Data Modeler ou Data Architect, id\u00e9alement dans un environnement corporate (\u00e9nergie, banque, retail, ou t\u00e9l\u00e9com)."""

    print("🔍 Extraction des compétences...")
    skills = extract_skills(texte, extractor)

    print("\n📌 Compétences détectées :")
    for s in skills:
        print(" -", s)
