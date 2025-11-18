import json
import spacy
from skillNer.skill_extractor_class import SkillExtractor
from spacy.matcher import PhraseMatcher

# ==========================================================
# Charger ton JSON et extraire toutes les surface forms
# ==========================================================
def extract_from_extractor( extractor, text, tresh=0.5):
    # `extractor.annotate` expects a raw string. Ensure we pass a string.
    res = extractor.annotate(text, tresh=tresh)

    skills = []
    for m in res['results'].get('full_matches', []):
        skills.append({
            "skill_id": m['skill_id'],
            "skill_name": extractor.skills_db[m['skill_id']]['skill_name'],
            "type": "full",
        })
    for m in res['results'].get('ngram_scored', []):
        skills.append({
            "skill_id": m['skill_id'],
            "skill_name": extractor.skills_db[m['skill_id']]['skill_name'],
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
    nlp = spacy.load("en_core_web_sm")
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
Mission Context
 
The organization is running a datacenter transition program aimed at regaining direct control over its hosting contracts. This requires the controlled relocation of existing infrastructure within current datacenter facilities, with a strong focus on:
Business continuity
Technical stability
A minimal-change approach (only essential updates; replacement of obsolete/unsupported components)
The scope includes datacenter, networking, network security, servers, storage, and virtualization.
 
Role Purpose
The Technical Expert supports internal infrastructure teams in:
Designing, configuring, and validating the technical target solution
Performing hands-on configuration, testing, and documentation
Collaborating closely with the internal technical lead to refine the architecture and migration strategy
👉 Physical installation or equipment movement inside the datacenters is not part of the role.
 
Key Responsibilities
Design and validate technical solutions for servers, storage, and VMware virtualization
Support migration preparation and validation testing
Configure and document all relevant infrastructure components
Produce high-quality technical documentation:
solution designs
configuration guides
migration procedures
Advise on backup and recovery strategy for current and future environments
Ensure efficient knowledge transfer to internal teams
Contribute to the stability-first, minimal-change philosophy
 
Required Skills & Experience
✔ Professional Background
Senior profile with 10+ years in datacenter infrastructure
✔ Technical Expertise
VMware: vSphere, vCenter, ESXi
Storage: Dell PowerStore, NetApp
Servers: Dell PowerEdge, HP ProLiant
Backup: StoreOnce (future solution TBD)
Operating Systems: Windows & Linux
✔ Core Competencies
Strong experience in solution design & enterprise implementations
Excellent analytical, documentation, and troubleshooting abilities
Ability to operate effectively in a complex, high-stakes program environment
 
Languages
French: preferred
English: required
Dutch: a plus
Work Mode
Hybrid (Brussels + remote)
Occasional visits to datacenter sites
Assignment Duration
Until June 2026, with possible extension until end of 2026
 
 """

    print("🔍 Extraction des compétences...")
    skills = extract_skills(texte, extractor)

    print("\n📌 Compétences détectées :")
    for s in skills:
        print(" -", s)
