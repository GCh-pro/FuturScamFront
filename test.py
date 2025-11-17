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
<p>NIRAS is de instelling die in België verantwoordelijk is voor het beheer van radioactief afval. Haar belangrijkste doelstelling is mens en milieu, vandaag en op zeer lange termijn, te beschermen tegen de mogelijke risico's die verbonden zijn aan het bestaan van radioactief afval. Wil je meer weten over onze activiteiten? Raadpleeg dan onze website <a href="https://www.niras.be">www.niras.be</a>.<br>&nbsp;<br>Als je wil bijdragen aan onze essentiële en uitdagende maatschappelijke opdracht, willen we je graag ontmoeten!</p>
<p>Om onze dienst ICT te versterken, zijn wij momenteel op zoek naar een Support/Infra Engineer.<br>&nbsp;<br>UW CONTACTPERSOON&nbsp;<br>Uw contactpersoon bij ProUnity voor deze aanvraag is Sara Ouaich. U kunt haar bereiken per mail via <a>niras@pro-unity.com</a><a>.&nbsp;</a></p>
<p>&nbsp;</p>
<p><strong>FUNCTIE</strong><br>Als Support/Infra Engineer ben jij de cruciale schakel tussen onze service desk en de technische teams. Met jouw expertise en servicegerichte aanpak zorg je voor een uitstekende dienstverlening, waarbij je de continuïteit en beveiliging van onze IT-omgeving waarborgt. Binnen ons enthousiaste team werk je actief mee aan nieuwe voorstellen om onze werking te optimaliseren met technologisch uitdagende oplossingen. Deze functie wordt on-site uitgevoerd op onze site te Dessel, met de mogelijkheid tot occasioneel telewerk.</p>
<p>Deze rol is drieledig:<br>o &nbsp; &nbsp;Service: Je biedt tweedelijns ondersteuning bij complexe IT-vraagstukken en problemen die niet door de eerstelijns support kunnen worden opgelost.<br>o &nbsp; &nbsp;Dagelijks beheer: Je bewaakt en onderhoudt netwerken, servers en platformen om een stabiele en veilige IT-omgeving te garanderen.<br>o &nbsp; &nbsp;Optimalisatie: Je werkt actief mee aan verbeteringen en configuraties met duidelijke deliverables om de IT-omgeving continu te verbeteren.<br>Je functioneert goed binnen een team, maar kan ook zelfstandig en nauwkeurig werken.<br>Je werkt gestructureerd, neemt initiatief en toont flexibiliteit.<br>Je bent communicatief vaardig en houdt altijd de behoeften van de interne klant centraal.<br>Jouw manier van werken sluit naadloos aan bij onze kernwaarden: veiligheid, verantwoordelijkheid, betrouwbaarheid en samenwerking.</p>
<p><strong>JOUW VERANTWOORDELIJKHEDEN:</strong></p>
<p>Technische vaardigheden<br>Kan complexe IT-problemen analyseren en oplossen die niet door de 1st line kunnen worden afgehandeld.<br>Degelijke kennis van netwerken (WAN, LAN, VPN, 802.1X, firewall) en systemen (Windows, Linux, Active Directory, M365, virtualisatie, storage)<br>Ervaring met werkstations, servers, randapparatuur en software-installaties/upgrades.<br>Kennis van cybersecurity best practices zoals patchmanagement en endpoint security (Security-bewustzijn).<br>Ervaring met PowerShell om terugkerende taken te automatiseren.<br>&nbsp;<br>Klant- en servicegerichtheid<br>Sterke communicatievaardigheden, kan helder en geduldig uitleggen aan niet-technische gebruikers.<br>Empathie en klantgericht denken, begrijpt de impact van IT-incidenten en stelt de gebruiker gerust.<br>Kan kalm blijven en prioriteiten stellen, ook onder druk.<br>&nbsp;<br>Analytisch en oplossingsgericht denken<br>Kan een degelijke root cause analyse toepassen en storingen systematisch oplossen.<br>Is kritisch, kan zelfstandig werken en out of the box oplossingen voorstellen.<br>&nbsp;<br>Samenwerking en documentatie<br>Werkt goed samen met 1st, 2nd en 3rd line engineers en andere afdelingen.<br>Heeft goeie documentatievaardigheden en houdt IT-processen (aanvragen, incidenten, root-cause analyse, ...) goed bij in een ticketingsysteem.<br>&nbsp;<br>Monitoring en proactief beheer<br>Is vertrouwd met systeem -en netwerkmonitoring tools of ingebouwde monitoring in cloudoplossingen.<br>Kan logs uit Windows Event Viewer, Syslog en andere tools analyseren om proactief issues te signaleren.<br>Houdt prestaties en gebruikstrends in de gaten om toekomstige wijzigingen aan te vragen of te plannen.<br>Reageert op monitoring-alerts en onderneemt proactieve acties om downtime te minimaliseren.</p>
<p>&nbsp;</p>
<p><strong>Waarom kiezen voor een opdracht bij NIRAS</strong><br>Als enige beheerder van radioactief afval in België biedt NIRAS je een unieke werkomgeving, waarin al onze medewerkers met passie en professionalisme naar duurzame oplossingen streven. We werken in het belang van de gemeenschap, het milieu en de toekomstige generaties, en met respect voor de regelgeving en de wetenschappelijke vooruitgang. De band die ons bindt is de maatschappelijke meerwaarde van onze opdracht.<br>&nbsp;</p>
 """

    print("🔍 Extraction des compétences...")
    skills = extract_skills(texte, extractor)

    print("\n📌 Compétences détectées :")
    for s in skills:
        print(" -", s)
