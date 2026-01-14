# Documentation Technique - FuturScam API

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation et Configuration](#installation-et-configuration)
4. [Modèles de données](#modèles-de-données)
5. [API Endpoints](#api-endpoints)
6. [Modules et Composants](#modules-et-composants)
7. [Sécurité](#sécurité)
8. [Performance et Optimisations](#performance-et-optimisations)
9. [Déploiement](#déploiement)
10. [Maintenance et Monitoring](#maintenance-et-monitoring)
11. [Troubleshooting](#troubleshooting)

---

## Vue d'ensemble

### Description

**FuturScam API** est une API REST développée avec FastAPI permettant la gestion complète de RFP (Request for Proposal) avec des fonctionnalités avancées :

- **Gestion CRUD complète** pour les RFP et les utilisateurs
- **Extraction automatique de compétences** (skills) via IA/NLP avec skillNer
- **Système de staging** pour validation avant publication
- **Envoi d'emails** avec pièces jointes via Microsoft Graph API
- **Stockage MongoDB Atlas** pour une scalabilité cloud

### Technologies principales

| Technologie | Version | Usage |
|-------------|---------|-------|
| FastAPI | 0.104.1 | Framework API REST |
| Python | 3.11+ | Langage de programmation |
| MongoDB | 4.6.0 | Base de données NoSQL |
| skillNer | 1.0.3 | Extraction de compétences |
| spaCy | 3.8.10 | Traitement du langage naturel |
| MSAL | - | Authentification Microsoft |
| Uvicorn | 0.24.0 | Serveur ASGI |

### Caractéristiques techniques

- **Architecture asynchrone** avec support des timeouts
- **Validation de données** avec Pydantic
- **Documentation auto-générée** (Swagger/ReDoc)
- **Gestion des fichiers temporaires** pour les pièces jointes
- **Lazy loading** des composants lourds (IA, mail)
- **Timeouts configurables** (120s pour l'extraction de skills)

---

## Architecture

### Architecture globale

```
┌─────────────────┐
│   Client Apps   │
│ (Web/Mobile)    │
└────────┬────────┘
         │ HTTPS/REST
         ▼
┌─────────────────────────────────┐
│      FastAPI Application        │
│  ┌──────────────────────────┐  │
│  │   Route Handlers         │  │
│  │  /mongodb  /users        │  │
│  │  /staging  /skillboy     │  │
│  │  /mail     /health       │  │
│  └──────────┬───────────────┘  │
│             │                   │
│  ┌──────────▼───────────────┐  │
│  │   Business Logic         │  │
│  │  - Validation            │  │
│  │  - Data Processing       │  │
│  │  - Error Handling        │  │
│  └──────────┬───────────────┘  │
└─────────────┼───────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌─────────┐
│MongoDB │ │spaCy │ │MS Graph │
│ Atlas  │ │skillNer│ │  API   │
└────────┘ └──────┘ └─────────┘
```

### Structure des collections MongoDB

#### Collection: `RFP` (Production)
Stocke les offres d'emploi validées et actives.

#### Collection: `StagingRFP`
Stocke les offres en cours de validation avant publication.

#### Collection: `Users`
Stocke les comptes utilisateurs de la plateforme.

### Flux de données

```
1. Client Request
   ↓
2. FastAPI Route Handler
   ↓
3. Pydantic Validation
   ↓
4. Business Logic Processing
   ↓
5. Database/External Service Call
   ↓
6. Response Formatting
   ↓
7. Client Response
```

---

## Installation et Configuration

### Prérequis système

- **Python** : 3.11 ou supérieur
- **MongoDB Atlas** : Compte actif avec cluster configuré
- **Azure AD** : Application enregistrée (pour l'envoi d'emails)
- **RAM** : Minimum 2 GB (4 GB recommandé pour skillNer)
- **Espace disque** : 500 MB minimum

### Installation pas à pas

#### 1. Cloner le repository

```bash
git clone <repository-url>
cd FuturScamFront
```

#### 2. Créer un environnement virtuel

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

#### 4. Télécharger le modèle spaCy

```bash
python -m spacy download en_core_web_sm
```

#### 5. Configuration des variables d'environnement

Éditer le fichier `params.py` :

```python
# MongoDB Configuration
MONGO_URI = "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/"
DB_NAME = "FuturScam"
COLLECTION_NAME = "RFP"

# Azure/Microsoft Graph Configuration
AZURE_CLIENT = "<your-client-id>"
AZURE_URI = "https://login.microsoftonline.com/<tenant-id>"
AZURE_SECRET = "<your-client-secret>"
AZURE_MAILBOX = "<sender-email@domain.com>"
```

⚠️ **Sécurité** : Ne jamais commiter `params.py` avec des credentials réels. Utiliser des variables d'environnement en production.

#### 6. Vérifier les fichiers de données

Assurez-vous que ces fichiers sont présents :
- `skill_db_optimized_20.json` : Base de données des compétences
- `token_dist.json` : Distributions de tokens pour skillNer

### Configuration MongoDB Atlas

#### 1. Créer les collections

```javascript
// Se connecter à MongoDB Atlas et créer les collections
use FuturScam

db.createCollection("RFP")
db.createCollection("StagingRFP")
db.createCollection("Users")
```

#### 2. Créer les index

```javascript
// Index pour performance
db.RFP.createIndex({ "job_id": 1 }, { unique: true })
db.RFP.createIndex({ "company.name": 1 })
db.RFP.createIndex({ "isActive": 1 })
db.RFP.createIndex({ "publishedAt": -1 })

db.StagingRFP.createIndex({ "job_id": 1 }, { unique: true })

db.Users.createIndex({ "id": 1 }, { unique: true })
db.Users.createIndex({ "mail": 1 }, { unique: true })
```

### Configuration Azure AD (pour emails)

#### 1. Enregistrer une application

1. Aller sur [Azure Portal](https://portal.azure.com)
2. Azure Active Directory → App registrations → New registration
3. Noter le **Client ID** et **Tenant ID**

#### 2. Créer un client secret

1. Dans votre application → Certificates & secrets
2. New client secret
3. Copier la **Value** (client secret)

#### 3. Configurer les permissions API

Ajouter les permissions Microsoft Graph suivantes :
- `Mail.Send` (Application permission)
- `User.Read.All` (optionnel, pour validation)

#### 4. Consentement administrateur

Un administrateur doit accorder le consentement pour les permissions d'application.

---

## Modèles de données

### JobDocument (RFP)

Modèle principal pour les offres d'emploi.

```python
{
    "job_id": "string (unique)",          # Identifiant unique de l'offre
    "roleTitle": "string",                # Titre du poste
    "job_desc": "string",                 # Description complète
    "company": {
        "name": "string",                 # Nom de l'entreprise
        "city": "string",                 # Ville
        "country": "string",              # Pays
        "street": "string",               # Rue
        "zipcode": "string",              # Code postal
        "region": "string"                # Région (optionnel)
    },
    "conditions": {
        "dailyRate": {
            "currency": "€",              # Devise
            "min": float,                 # TJM minimum
            "max": float                  # TJM maximum
        },
        "fixedMargin": float,             # Marge fixe
        "fromAt": "string (ISO date)",    # Date de début
        "toAt": "string (ISO date)",      # Date de fin
        "startImmediately": boolean,      # Démarrage immédiat
        "occupation": "string"            # Taux d'occupation
    },
    "skills": [
        {
            "name": "string",             # Nom de la compétence
            "seniority": "string"         # Niveau (Junior/Senior/Expert)
        }
    ],
    "languages": [
        {
            "language": "string",         # Langue
            "level": "string"             # Niveau (A1-C2, Fluent, etc.)
        }
    ],
    "serviceProvider": "string",          # Prestataire
    "deadlineAt": "string (ISO date)",    # Date limite de candidature
    "publishedAt": "string (ISO date)",   # Date de publication
    "metadata": [                         # Métadonnées additionnelles
        {"key": "value"}
    ],
    "job_url": "string (URL)",            # Lien vers l'annonce
    "remoteOption": "string",             # Télétravail (Full/Partial/None)
    "seniority": "string",                # Niveau de séniorité requis
    "isActive": boolean,                  # Offre active ou archivée
    "RFP_type": "string"                  # Type de RFP
}
```

### User

Modèle pour les utilisateurs de la plateforme.

```python
{
    "id": "string (unique)",              # Identifiant unique
    "name": "string",                     # Nom complet
    "mail": "string (email)",             # Email (unique)
    "company": "string",                  # Entreprise
    "role": "string",                     # Rôle/Poste
    "password": "string",                 # Mot de passe (à hacher en prod!)
    "metadata": [                         # Données additionnelles
        {"key": "value"}
    ]
}
```

⚠️ **Note de sécurité** : Le mot de passe est actuellement stocké en clair. **Il est impératif d'implémenter un hashage** (bcrypt, Argon2) en production.

### SkillExtractionRequest

```python
{
    "text": "string"                      # Texte à analyser (max recommandé: 10000 chars)
}
```

### SkillExtractionResponse

```python
{
    "skills": ["string"],                 # Compétences techniques détectées
    "languages": ["string"],              # Langues détectées
    "skills_count": int,                  # Nombre de compétences
    "languages_count": int                # Nombre de langues
}
```

---

## API Endpoints

### Base URL

```
http://localhost:8000
```

En production : `https://your-domain.com`

### Documentation interactive

- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`

---

### 1. Health & Status

#### GET /health

Vérification de l'état de l'API.

**Response:**
```json
{
    "status": "ok",
    "message": "FuturScam API is running"
}
```

**Status codes:**
- `200` : API opérationnelle

---

#### GET /

Informations sur l'API et liste des endpoints disponibles.

**Response:**
```json
{
    "name": "FuturScam API",
    "version": "1.0.0",
    "endpoints": {
        "health": "GET /health - API health check",
        "mail": "POST /mail - Send email with attachments",
        "mongodb": {...},
        "skillboy": {...}
    }
}
```

---

### 2. MongoDB - Gestion des RFP (Production)

#### GET /mongodb

Récupère tous les RFP de production.

**Response:**
```json
{
    "count": 42,
    "data": [
        {
            "_id": "507f1f77bcf86cd799439011",
            "job_id": "JOB-2025-001",
            "roleTitle": "Senior Data Engineer",
            ...
        }
    ]
}
```

**Status codes:**
- `200` : Succès
- `500` : Erreur serveur/base de données

---

#### GET /mongodb/{job_id}

Récupère un RFP spécifique par son `job_id`.

**Parameters:**
- `job_id` (path) : Identifiant unique du job

**Response:**
```json
{
    "_id": "507f1f77bcf86cd799439011",
    "job_id": "JOB-2025-001",
    "roleTitle": "Senior Data Engineer",
    "company": {...},
    ...
}
```

**Status codes:**
- `200` : Succès
- `404` : RFP non trouvé
- `400` : Paramètre invalide

---

#### POST /mongodb

Crée un nouveau RFP.

**Request Body:**
```json
{
    "job_id": "JOB-2025-042",
    "roleTitle": "DevOps Engineer",
    "job_desc": "We are looking for...",
    "company": {
        "name": "TechCorp",
        "city": "Brussels",
        "country": "Belgium"
    },
    "conditions": {
        "dailyRate": {
            "currency": "€",
            "min": 500,
            "max": 700
        },
        "fromAt": "2025-02-01",
        "toAt": "2025-08-01",
        "startImmediately": false,
        "occupation": "100%"
    },
    "deadlineAt": "2025-01-31",
    "publishedAt": "2025-01-14",
    "isActive": true,
    "skills": [
        {"name": "Kubernetes", "seniority": "Expert"},
        {"name": "Docker", "seniority": "Advanced"}
    ],
    "languages": [
        {"language": "English", "level": "Fluent"}
    ]
}
```

**Response:**
```json
{
    "message": "Job posted successfully",
    "id": "507f1f77bcf86cd799439011"
}
```

**Status codes:**
- `200` : Succès
- `400` : Données invalides

---

#### PUT /mongodb/{job_id}

Met à jour un RFP existant. Seuls les champs fournis sont modifiés.

**Parameters:**
- `job_id` (path) : Identifiant du job à modifier

**Request Body (exemple partiel):**
```json
{
    "isActive": false,
    "conditions": {
        "dailyRate": {
            "max": 750
        }
    }
}
```

**Response:**
```json
{
    "message": "Job updated successfully",
    "modified_count": 1
}
```

**Status codes:**
- `200` : Succès
- `400` : Aucun champ à modifier ou données invalides
- `404` : RFP non trouvé

---

#### DELETE /mongodb/{job_id}

Supprime définitivement un RFP.

**Parameters:**
- `job_id` (path) : Identifiant du job

**Response:**
```json
{
    "message": "Job deleted successfully",
    "deleted_count": 1
}
```

**Status codes:**
- `200` : Succès
- `404` : RFP non trouvé

---

### 3. Staging - Gestion des RFP en validation

Les endpoints `/staging` fonctionnent exactement comme `/mongodb` mais opèrent sur la collection `StagingRFP`.

- `GET /staging` : Liste tous les RFP en staging
- `GET /staging/{job_id}` : Récupère un RFP en staging
- `POST /staging` : Crée un RFP en staging
- `PUT /staging/{job_id}` : Modifie un RFP en staging
- `DELETE /staging/{job_id}` : Supprime un RFP en staging

**Cas d'usage** : Permet de valider/modifier les RFP avant publication en production.

---

### 4. Users - Gestion des utilisateurs

#### GET /users

Récupère tous les utilisateurs.

**Response:**
```json
{
    "count": 15,
    "data": [
        {
            "_id": "507f1f77bcf86cd799439011",
            "id": "user-001",
            "name": "John Doe",
            "mail": "john.doe@example.com",
            "company": "TechCorp",
            "role": "Recruiter",
            ...
        }
    ]
}
```

---

#### GET /users/{user_id}

Récupère un utilisateur spécifique.

**Parameters:**
- `user_id` (path) : ID de l'utilisateur

**Status codes:**
- `200` : Succès
- `404` : Utilisateur non trouvé

---

#### POST /users

Crée un nouvel utilisateur.

**Request Body:**
```json
{
    "id": "user-042",
    "name": "Jane Smith",
    "mail": "jane.smith@company.com",
    "company": "DataCorp",
    "role": "HR Manager",
    "password": "temporaryPassword123",
    "metadata": []
}
```

**Response:**
```json
{
    "message": "User created successfully",
    "id": "507f1f77bcf86cd799439011"
}
```

**Status codes:**
- `200` : Succès
- `400` : Utilisateur avec cet ID existe déjà

⚠️ **Sécurité** : Implémenter un hashage de mot de passe en production !

---

#### PUT /users/{user_id}

Met à jour un utilisateur.

**Request Body (exemple):**
```json
{
    "role": "Senior Recruiter",
    "company": "NewCorp"
}
```

**Status codes:**
- `200` : Succès
- `400` : Aucun champ à modifier
- `404` : Utilisateur non trouvé

---

#### DELETE /users/{user_id}

Supprime un utilisateur.

**Status codes:**
- `200` : Succès
- `404` : Utilisateur non trouvé

---

### 5. SkillBoy - Extraction de compétences (IA)

#### POST /skillboy

Extrait automatiquement les compétences et langues d'un texte.

**Timeout** : 120 secondes

**Request Body:**
```json
{
    "text": "We are looking for a Senior Python Developer with experience in Docker, Kubernetes, AWS, and fluent in English and French language."
}
```

**Response:**
```json
{
    "skills": [
        "Python",
        "Docker",
        "Kubernetes",
        "AWS"
    ],
    "languages": [
        "English language",
        "French language"
    ],
    "skills_count": 4,
    "languages_count": 2
}
```

**Status codes:**
- `200` : Succès
- `400` : Texte vide
- `503` : Extracteur non chargé
- `504` : Timeout (texte trop long ou complexe)

**Limitations** :
- Textes recommandés : < 10 000 caractères
- Timeout : 120 secondes maximum
- Langue supportée : Anglais principalement

---

#### GET /skillboy/health

Vérifie si l'extracteur de compétences est chargé et prêt.

**Response:**
```json
{
    "status": "ready",
    "message": "Skill extractor is ready"
}
```

ou

```json
{
    "status": "not_loaded",
    "message": "Skill extractor not loaded"
}
```

---

### 6. Mail - Envoi d'emails

#### POST /mail

Envoie un email avec pièces jointes via Microsoft Graph API.

**Content-Type** : `multipart/form-data`

**Parameters:**

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| to_addresses | string | ✅ | Emails destinataires (séparés par virgules) |
| subject | string | ✅ | Sujet de l'email |
| body | string | ✅ | Corps de l'email (HTML ou texte) |
| cc_addresses | string | ❌ | Destinataires en copie (CC) |
| bcc_addresses | string | ❌ | Destinataires en copie cachée (BCC) |
| is_html | boolean | ❌ | Format HTML (défaut: true) |
| attachments | file[] | ❌ | Fichiers à joindre (PDF, PNG, JPEG...) |

**Exemple cURL:**

```bash
curl -X POST "http://localhost:8000/mail" \
  -F "to_addresses=recipient@example.com,another@example.com" \
  -F "subject=Job Opportunity" \
  -F "body=<h1>Hello!</h1><p>We have a great opportunity...</p>" \
  -F "is_html=true" \
  -F "attachments=@document.pdf" \
  -F "attachments=@image.png"
```

**Response:**
```json
{
    "status": "success",
    "message": "Email sent successfully to recipient@example.com, another@example.com",
    "recipients": {
        "to": ["recipient@example.com", "another@example.com"],
        "cc": null,
        "bcc": null
    },
    "attachments_count": 2
}
```

**Status codes:**
- `200` : Email envoyé avec succès
- `400` : Paramètres invalides
- `500` : Erreur d'envoi

**Limitations** :
- Taille max par pièce jointe : **25 MB**
- Formats supportés : tous (PDF, DOCX, PNG, JPEG, etc.)
- Les fichiers temporaires sont automatiquement supprimés après envoi

---

## Modules et Composants

### main.py

Fichier principal de l'application FastAPI.

**Responsabilités** :
- Définition des routes et endpoints
- Initialisation de l'application FastAPI
- Chargement du skill extractor au startup
- Gestion des connexions MongoDB
- Orchestration des différents modules

**Points clés** :

```python
# Lazy loading du mail sender
mail_sender_instance = None

def get_mail_sender():
    global mail_sender_instance
    if mail_sender_instance is None:
        # Initialisation seulement au premier appel
        mail_sender_instance = MailSender(...)
    return mail_sender_instance
```

---

### test.py

Module d'extraction de compétences avec skillNer et spaCy.

**Fonctions principales** :

#### `load_skill_terms(json_path)`

Charge la base de données de compétences depuis un fichier JSON.

```python
skill_terms = load_skill_terms("skill_db_optimized_20.json")
# Retourne: Dict[str, Dict] avec skill_id -> skill_info
```

**Structure attendue du JSON** :

```json
{
    "skill_001": {
        "skill_name": "Python",
        "skill_type": "Hard Skill",
        ...
    }
}
```

#### `create_extractor(skill_terms)`

Crée et configure le SkillExtractor avec spaCy et token embeddings.

**Optimisations** :
- Désactivation du NER de spaCy (non nécessaire)
- Chargement des token distances depuis `token_dist.json`
- Initialisation des vecteurs avec seed stable pour reproductibilité

```python
nlp = spacy.load("en_core_web_sm", disable=["ner"])
extractor = SkillExtractor(nlp, skills_db=skill_terms, phraseMatcher=PhraseMatcher)
```

#### `extract_skills(text, extractor)`

Extrait les compétences d'un texte et retourne une liste dédupliquée.

**Paramètres** :
- `text` : Texte à analyser (string)
- `extractor` : Instance de SkillExtractor

**Retourne** : `List[str]` de compétences détectées

---

### mail_sender.py

Module d'envoi d'emails via Microsoft Graph API.

**Classe principale** : `MailSender`

#### Méthodes

##### `__init__(client_id, authority, client_secret, mailbox_email, scopes)`

Initialise le mail sender avec les credentials Azure.

##### `authenticate()`

Authentifie l'application via MSAL (Microsoft Authentication Library).

**Flow** :
1. Créer un `ConfidentialClientApplication`
2. Acquérir un token avec `acquire_token_for_client`
3. Stocker le token d'accès

**Permissions requises** : `Mail.Send` (Application)

##### `send_email(...)`

Envoie un email avec pièces jointes.

**Retourne** : `bool` (True si succès)

**Fonctionnalités** :
- Support des destinataires multiples (TO, CC, BCC)
- Pièces jointes multiples (encodage base64)
- Format HTML ou texte
- Validation de la taille (< 25 MB par fichier)

##### `_prepare_attachment(file_path)`

Prépare une pièce jointe pour l'envoi.

**Traitement** :
1. Vérification de l'existence du fichier
2. Vérification de la taille (< 25 MB)
3. Lecture et encodage en base64
4. Création de l'objet Graph API

---

### params.py

Fichier de configuration centralisé.

**Variables** :

```python
# MongoDB
MONGO_URI = "mongodb+srv://..."
DB_NAME = "FuturScam"
COLLECTION_NAME = "RFP"

# Azure AD / Microsoft Graph
AZURE_CLIENT = "client-id"
AZURE_URI = "https://login.microsoftonline.com/tenant-id"
AZURE_SECRET = "client-secret"
AZURE_MAILBOX = "sender@domain.com"
```

⚠️ **Important** : Ajouter `params.py` au `.gitignore` et utiliser des variables d'environnement en production.

---

## Sécurité

### Vulnérabilités actuelles

⚠️ **CRITIQUE** : Les points suivants doivent être corrigés en production :

#### 1. Mots de passe en clair

**Problème** : Les mots de passe utilisateurs sont stockés en texte clair.

**Solution** :

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash lors de la création
hashed_password = pwd_context.hash(user.password)

# Vérification lors de la connexion
pwd_context.verify(plain_password, hashed_password)
```

#### 2. Credentials hardcodés

**Problème** : Les credentials Azure et MongoDB sont dans `params.py`.

**Solution** : Utiliser des variables d'environnement.

```python
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
AZURE_CLIENT = os.getenv("AZURE_CLIENT_ID")
```

`.env` :
```
MONGO_URI=mongodb+srv://...
AZURE_CLIENT_ID=...
AZURE_SECRET=...
```

#### 3. Pas d'authentification sur les endpoints

**Problème** : Aucune authentification/autorisation n'est implémentée.

**Solution** : Ajouter JWT ou OAuth2.

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/mongodb")
def get_jobs(credentials: str = Depends(security)):
    # Vérifier le token JWT
    verify_token(credentials.credentials)
    ...
```

### Bonnes pratiques de sécurité

#### CORS (Cross-Origin Resource Sharing)

Ajouter une configuration CORS restrictive :

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Pas de "*" en prod
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

#### Rate Limiting

Protéger contre les abus :

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/skillboy")
@limiter.limit("10/minute")  # Max 10 requêtes/minute
async def extract_skills(...):
    ...
```

#### Validation des inputs

- Utiliser Pydantic pour toutes les entrées
- Valider les email addresses
- Sanitizer les chaînes de caractères
- Limiter la taille des uploads

#### HTTPS

Toujours utiliser HTTPS en production :

```bash
uvicorn main:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

#### Logging sécurisé

Ne jamais logger de données sensibles :

```python
import logging

# ✅ BON
logging.info(f"User {user_id} logged in")

# ❌ MAUVAIS
logging.info(f"User {user_id} with password {password} logged in")
```

---

## Performance et Optimisations

### Optimisations actuelles

#### 1. Lazy loading du skill extractor

Le modèle skillNer (~200 MB) est chargé une seule fois au startup.

```python
@app.on_event("startup")
def startup():
    global skill_terms, extractor
    skill_terms = load_skill_terms("skill_db_optimized_20.json")
    extractor = create_extractor(skill_terms)
```

#### 2. Lazy loading du mail sender

Le mail sender n'est initialisé qu'au premier appel.

```python
mail_sender_instance = None

def get_mail_sender():
    global mail_sender_instance
    if mail_sender_instance is None:
        mail_sender_instance = MailSender(...)
        mail_sender_instance.authenticate()
    return mail_sender_instance
```

#### 3. Async/await pour l'extraction

L'extraction de skills utilise `asyncio.to_thread` pour ne pas bloquer.

```python
skills = await asyncio.wait_for(
    asyncio.to_thread(extract_skills, request.text, extractor),
    timeout=120.0
)
```

#### 4. Index MongoDB

Des index sont créés sur les champs fréquemment recherchés :
- `job_id` (unique)
- `company.name`
- `isActive`
- `publishedAt`

### Optimisations recommandées

#### 1. Caching

Implémenter un cache pour les requêtes fréquentes :

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_job_cached(job_id: str):
    return get_collection().find_one({"job_id": job_id})
```

Ou utiliser Redis :

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_job_cached(job_id: str):
    # Vérifier le cache
    cached = redis_client.get(f"job:{job_id}")
    if cached:
        return json.loads(cached)
    
    # Sinon, récupérer de MongoDB
    job = get_collection().find_one({"job_id": job_id})
    redis_client.setex(f"job:{job_id}", 3600, json.dumps(job))
    return job
```

#### 2. Connection pooling MongoDB

```python
from pymongo import MongoClient

# Créer un client global avec pool
mongo_client = MongoClient(
    MONGO_URI,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=45000
)

def get_collection():
    return mongo_client[DB_NAME][COLLECTION_NAME]
```

#### 3. Compression des réponses

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### 4. Pagination pour les listes

```python
@app.get("/mongodb")
def get_all_jobs(skip: int = 0, limit: int = 50):
    collection = get_collection()
    docs = list(collection.find().skip(skip).limit(limit))
    total = collection.count_documents({})
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(docs),
        "data": docs
    }
```

#### 5. Background tasks pour emails

```python
from fastapi import BackgroundTasks

@app.post("/mail")
async def send_email(background_tasks: BackgroundTasks, ...):
    # Ajouter l'envoi en background
    background_tasks.add_task(send_email_task, to_list, subject, body, ...)
    
    return {
        "status": "queued",
        "message": "Email will be sent shortly"
    }
```

### Monitoring des performances

#### Temps de réponse

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### Métriques avec Prometheus

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

---

## Déploiement

### Déploiement local

#### Mode développement

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Options utiles :
- `--reload` : Rechargement automatique lors des modifications
- `--log-level debug` : Logs détaillés

#### Mode production local

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

- `--workers 4` : 4 processus workers (CPU cores)
- `--timeout-keep-alive 120` : Timeout pour les connexions keep-alive

### Déploiement Docker

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Télécharger le modèle spaCy
RUN python -m spacy download en_core_web_sm

# Copier le code de l'application
COPY . .

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGO_URI=${MONGO_URI}
      - AZURE_CLIENT=${AZURE_CLIENT}
      - AZURE_SECRET=${AZURE_SECRET}
      - AZURE_URI=${AZURE_URI}
      - AZURE_MAILBOX=${AZURE_MAILBOX}
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./skill_db_optimized_20.json:/app/skill_db_optimized_20.json:ro
      - ./token_dist.json:/app/token_dist.json:ro
```

#### Démarrer avec Docker Compose

```bash
docker-compose up -d
```

### Déploiement Cloud

#### Azure App Service

1. Créer une App Service :
```bash
az webapp up --name futurscam-api --runtime "PYTHON:3.11"
```

2. Configurer les variables d'environnement :
```bash
az webapp config appsettings set --name futurscam-api \
    --settings MONGO_URI="mongodb+srv://..."
```

3. Déployer :
```bash
az webapp deployment source config-zip --name futurscam-api --src app.zip
```

#### AWS Elastic Beanstalk

1. Créer un environnement :
```bash
eb init -p python-3.11 futurscam-api
eb create futurscam-api-env
```

2. Déployer :
```bash
eb deploy
```

#### Google Cloud Run

```bash
# Build l'image
gcloud builds submit --tag gcr.io/project-id/futurscam-api

# Déployer
gcloud run deploy futurscam-api \
    --image gcr.io/project-id/futurscam-api \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated
```

### Reverse Proxy avec Nginx

```nginx
server {
    listen 80;
    server_name api.futurscam.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout pour skillboy
        proxy_read_timeout 180s;
        proxy_connect_timeout 180s;
    }
}
```

### SSL/TLS avec Let's Encrypt

```bash
# Installer certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtenir un certificat
sudo certbot --nginx -d api.futurscam.com

# Renouvellement automatique
sudo certbot renew --dry-run
```

---

## Maintenance et Monitoring

### Logging

#### Configuration des logs

```python
import logging
from logging.handlers import RotatingFileHandler

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Utilisation
logger.info("API started")
logger.error(f"Error processing job {job_id}: {error}")
```

#### Logs structurés avec JSON

```python
import json_logging

json_logging.init_fastapi(enable_json=True)
json_logging.init_request_instrument(app)
```

### Health Checks avancés

```python
@app.get("/health/detailed")
def health_check_detailed():
    status = {
        "api": "ok",
        "mongodb": "unknown",
        "skillboy": "unknown",
        "mail": "unknown"
    }
    
    # Test MongoDB
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info()
        status["mongodb"] = "ok"
    except Exception as e:
        status["mongodb"] = f"error: {str(e)}"
    
    # Test Skillboy
    status["skillboy"] = "ready" if extractor else "not_loaded"
    
    # Test Mail (sans envoyer)
    try:
        sender = get_mail_sender()
        status["mail"] = "ok" if sender.access_token else "not_authenticated"
    except Exception as e:
        status["mail"] = f"error: {str(e)}"
    
    overall = "ok" if all(v == "ok" or v == "ready" for v in status.values()) else "degraded"
    
    return {
        "status": overall,
        "components": status,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Métriques personnalisées

```python
from prometheus_client import Counter, Histogram

# Compteurs
skill_extractions = Counter(
    'skill_extractions_total',
    'Total number of skill extractions'
)

emails_sent = Counter(
    'emails_sent_total',
    'Total number of emails sent',
    ['status']  # success/failure
)

# Histogrammes pour la latence
extraction_duration = Histogram(
    'skill_extraction_duration_seconds',
    'Time spent extracting skills'
)

# Utilisation
@app.post("/skillboy")
async def extract_skills_from_text(request: SkillExtractionRequest):
    skill_extractions.inc()
    
    with extraction_duration.time():
        skills = await extract_skills(...)
    
    return skills
```

### Alertes

#### Alertes par email

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = f"[ALERT] {subject}"
    msg['From'] = "alerts@futurscam.com"
    msg['To'] = "admin@futurscam.com"
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login("alerts@futurscam.com", "password")
        server.send_message(msg)

# Utilisation
@app.on_event("startup")
def startup():
    try:
        global skill_terms, extractor
        skill_terms = load_skill_terms("skill_db_optimized_20.json")
        extractor = create_extractor(skill_terms)
    except Exception as e:
        send_alert("Skill Extractor Failed", f"Error: {str(e)}")
        raise
```

### Backup MongoDB

#### Script de backup automatique

```bash
#!/bin/bash

# backup_mongodb.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"
DB_NAME="FuturScam"

mkdir -p $BACKUP_DIR

mongodump --uri="$MONGO_URI" \
    --db=$DB_NAME \
    --out=$BACKUP_DIR/$DATE

# Compression
tar -czf $BACKUP_DIR/$DATE.tar.gz -C $BACKUP_DIR $DATE
rm -rf $BACKUP_DIR/$DATE

# Garder seulement les 7 derniers jours
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE.tar.gz"
```

#### Cron job

```cron
# Backup quotidien à 2h du matin
0 2 * * * /path/to/backup_mongodb.sh
```

---

## Troubleshooting

### Problèmes fréquents

#### 1. Skill extractor ne se charge pas

**Symptômes** :
- `POST /skillboy` retourne 503
- Message : "Skill extractor not loaded"

**Solutions** :

1. Vérifier que `skill_db_optimized_20.json` existe :
```bash
ls -lh skill_db_optimized_20.json
```

2. Vérifier le modèle spaCy :
```bash
python -m spacy validate
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('OK')"
```

3. Vérifier les logs au startup :
```bash
uvicorn main:app --log-level debug
```

4. Tester manuellement :
```python
from test import load_skill_terms, create_extractor

skill_terms = load_skill_terms("skill_db_optimized_20.json")
print(f"Loaded {len(skill_terms)} skills")

extractor = create_extractor(skill_terms)
print("Extractor created successfully")
```

---

#### 2. Timeout sur /skillboy

**Symptômes** :
- Status 504
- Message : "Skill extraction timed out after 120 seconds"

**Solutions** :

1. **Réduire la taille du texte** :
```python
# Limiter à 5000 caractères
text = request.text[:5000]
```

2. **Augmenter le timeout** :
```python
skills = await asyncio.wait_for(
    asyncio.to_thread(extract_skills, request.text, extractor),
    timeout=300.0  # 5 minutes
)
```

3. **Optimiser le modèle** :
- Utiliser `skill_db_optimized_20.json` au lieu de `skill_db_relax_20.json`
- Réduire le nombre de skills dans la base

4. **Augmenter les ressources** :
- Plus de RAM (minimum 4 GB)
- Plus de CPU cores

---

#### 3. Erreur MongoDB "Connection timeout"

**Symptômes** :
- 500 Internal Server Error
- `pymongo.errors.ServerSelectionTimeoutError`

**Solutions** :

1. **Vérifier la chaîne de connexion** :
```python
# params.py
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"

# Tester la connexion
from pymongo import MongoClient
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
print(client.server_info())
```

2. **Vérifier les IP autorisées** :
- Aller sur MongoDB Atlas
- Network Access → Add IP Address
- Autoriser `0.0.0.0/0` (développement uniquement)

3. **Vérifier les credentials** :
- Username correct
- Password correct (attention aux caractères spéciaux : encoder en URL)

```python
from urllib.parse import quote_plus

username = quote_plus("user@domain.com")
password = quote_plus("p@ssw0rd!")
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster.mongodb.net/"
```

---

#### 4. Emails ne s'envoient pas

**Symptômes** :
- 500 Internal Server Error sur `/mail`
- "Failed to send email" ou "Not authenticated"

**Solutions** :

1. **Vérifier l'authentification Azure** :
```python
from params import AZURE_CLIENT, AZURE_URI, AZURE_SECRET
from mail_sender import MailSender

sender = MailSender(
    client_id=AZURE_CLIENT,
    authority=AZURE_URI,
    client_secret=AZURE_SECRET,
    mailbox_email="sender@domain.com",
    scopes=["https://graph.microsoft.com/.default"]
)

try:
    sender.authenticate()
    print("✅ Authentication successful")
    print(f"Token: {sender.access_token[:50]}...")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
```

2. **Vérifier les permissions Graph API** :
- Aller sur Azure Portal
- App registrations → Votre app → API permissions
- Vérifier que `Mail.Send` (Application) est présente
- Vérifier que le consentement admin est accordé (✅)

3. **Vérifier le secret** :
- Le secret Azure n'a pas expiré
- Le secret est correctement copié (sans espaces)

4. **Tester manuellement** :
```bash
curl -X POST "http://localhost:8000/mail" \
  -F "to_addresses=test@example.com" \
  -F "subject=Test Email" \
  -F "body=Hello World" \
  -F "is_html=false"
```

---

#### 5. Fichiers temporaires ne se supprimant pas

**Symptômes** :
- Espace disque qui se remplit
- Dossier `/tmp` plein de fichiers

**Solutions** :

1. **Vérifier la suppression dans le code** :
```python
finally:
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except Exception as e:
            print(f"[WARN] Error deleting temp file: {e}")
```

2. **Nettoyer manuellement** :
```bash
# Linux/Mac
find /tmp -name "tmp*" -mtime +1 -delete

# Windows
forfiles /P %TEMP% /S /D -1 /C "cmd /c del @path"
```

3. **Configurer un cleanup automatique** :
```python
import atexit
import tempfile
import shutil

temp_dir = tempfile.mkdtemp()

@atexit.register
def cleanup():
    shutil.rmtree(temp_dir, ignore_errors=True)
```

---

#### 6. Erreur "Job already exists"

**Symptômes** :
- Status 400 sur `POST /mongodb`
- Message : Duplicate key error

**Solutions** :

1. **Utiliser un `job_id` unique** :
```python
import uuid

job_id = f"JOB-{uuid.uuid4().hex[:8]}"
```

2. **Vérifier avant d'insérer** :
```python
existing = collection.find_one({"job_id": job.job_id})
if existing:
    raise HTTPException(status_code=400, detail="Job ID already exists")
```

3. **Utiliser upsert** :
```python
collection.update_one(
    {"job_id": job.job_id},
    {"$set": job.model_dump()},
    upsert=True
)
```

---

### Debug mode

Activer le mode debug pour plus d'informations :

```python
# main.py
app = FastAPI(debug=True)

# Démarrage
uvicorn main:app --reload --log-level debug
```

### Tests de charge

#### Avec Apache Bench

```bash
# Tester /health (100 requêtes, 10 concurrentes)
ab -n 100 -c 10 http://localhost:8000/health

# Tester POST /mongodb
ab -n 50 -c 5 -p job.json -T application/json http://localhost:8000/mongodb
```

#### Avec Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class FuturScamUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_jobs(self):
        self.client.get("/mongodb")
    
    @task(1)
    def extract_skills(self):
        self.client.post("/skillboy", json={
            "text": "Looking for Python developer with Docker experience"
        })

# Démarrer
locust -f locustfile.py
```

---

## Annexes

### A. Exemples de requêtes complètes

#### Créer un RFP complet

```bash
curl -X POST "http://localhost:8000/mongodb" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "JOB-2025-042",
    "roleTitle": "Senior DevOps Engineer",
    "job_desc": "We are seeking an experienced DevOps Engineer to join our cloud infrastructure team. The ideal candidate will have strong experience with Kubernetes, Docker, and AWS.",
    "company": {
      "name": "TechCorp International",
      "city": "Brussels",
      "country": "Belgium",
      "street": "Avenue Louise 123",
      "zipcode": "1050",
      "region": "Brussels-Capital"
    },
    "conditions": {
      "dailyRate": {
        "currency": "€",
        "min": 550,
        "max": 750
      },
      "fixedMargin": 0,
      "fromAt": "2025-03-01",
      "toAt": "2025-09-01",
      "startImmediately": false,
      "occupation": "100%"
    },
    "skills": [
      {"name": "Kubernetes", "seniority": "Expert"},
      {"name": "Docker", "seniority": "Expert"},
      {"name": "AWS", "seniority": "Advanced"},
      {"name": "Terraform", "seniority": "Advanced"},
      {"name": "Python", "seniority": "Intermediate"}
    ],
    "languages": [
      {"language": "English", "level": "Fluent"},
      {"language": "French", "level": "Intermediate"}
    ],
    "serviceProvider": "DevOps Solutions BVBA",
    "deadlineAt": "2025-02-15",
    "publishedAt": "2025-01-14",
    "job_url": "https://jobs.techcorp.com/devops-042",
    "remoteOption": "Hybrid",
    "seniority": "Senior",
    "isActive": true,
    "RFP_type": "Contract",
    "metadata": [
      {"key": "industry", "value": "Technology"},
      {"key": "team_size", "value": "12"},
      {"key": "urgency", "value": "high"}
    ]
  }'
```

#### Extraire les compétences

```bash
curl -X POST "http://localhost:8000/skillboy" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We are looking for a Senior Full Stack Developer with 5+ years of experience in React, Node.js, TypeScript, and PostgreSQL. Experience with Docker and Kubernetes is a plus. Must be fluent in English and French."
  }'
```

#### Envoyer un email avec pièce jointe

```bash
curl -X POST "http://localhost:8000/mail" \
  -F "to_addresses=candidate@example.com" \
  -F "subject=Job Opportunity - Senior DevOps Engineer" \
  -F "body=<h1>Job Opportunity</h1><p>Dear Candidate,</p><p>We have an exciting opportunity for you...</p>" \
  -F "cc_addresses=hr@techcorp.com" \
  -F "is_html=true" \
  -F "attachments=@job_description.pdf"
```

### B. Structure de la base de compétences

Le fichier `skill_db_optimized_20.json` contient environ 5000-10000 compétences.

**Format** :

```json
{
  "skill_00001": {
    "skill_name": "Python",
    "skill_type": "Hard Skill",
    "skill_category": "Programming Language",
    "skill_len": 1,
    "surface_forms": [
      "Python",
      "python",
      "Python programming",
      "Python development"
    ]
  },
  "skill_00002": {
    "skill_name": "Docker",
    "skill_type": "Hard Skill",
    "skill_category": "DevOps Tool",
    "skill_len": 1,
    "surface_forms": [
      "Docker",
      "docker",
      "Docker containers",
      "Dockerization"
    ]
  }
}
```

### C. Variables d'environnement recommandées

Créer un fichier `.env` pour la production :

```bash
# MongoDB
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=FuturScam
COLLECTION_NAME=RFP

# Azure AD
AZURE_CLIENT_ID=<client-id>
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_SECRET=<secret>
AZURE_MAILBOX=sender@domain.com

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_TIMEOUT=120

# Security
JWT_SECRET_KEY=<random-secret-key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/futurscam/api.log

# Performance
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
```

Charger dans Python :

```python
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
AZURE_CLIENT = os.getenv("AZURE_CLIENT_ID")
# ...
```

### D. Checklist de déploiement

- [ ] Variables d'environnement configurées
- [ ] `params.py` ajouté au `.gitignore`
- [ ] Hachage des mots de passe implémenté
- [ ] HTTPS configuré (certificat SSL/TLS)
- [ ] CORS configuré de manière restrictive
- [ ] Rate limiting activé
- [ ] Authentification JWT implémentée
- [ ] Logs structurés configurés
- [ ] Monitoring (Prometheus/Grafana) activé
- [ ] Health checks configurés
- [ ] Backups MongoDB automatisés
- [ ] Alertes configurées (email/Slack)
- [ ] Documentation à jour
- [ ] Tests d'intégration passants
- [ ] Tests de charge effectués
- [ ] Plan de rollback défini

---

## Conclusion

Cette documentation technique couvre l'ensemble des aspects de l'API FuturScam :

✅ **Architecture** : Structure modulaire avec séparation des responsabilités
✅ **Installation** : Procédure complète avec tous les prérequis
✅ **API Reference** : Documentation détaillée de tous les endpoints
✅ **Sécurité** : Points d'attention et bonnes pratiques
✅ **Performance** : Optimisations actuelles et recommandations
✅ **Déploiement** : Options multiples (local, Docker, cloud)
✅ **Maintenance** : Logging, monitoring, backup
✅ **Troubleshooting** : Solutions aux problèmes courants

### Ressources supplémentaires

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [skillNer GitHub](https://github.com/AnasAito/SkillNER)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [spaCy Documentation](https://spacy.io/)

### Support

Pour toute question ou problème :
- 📧 Email : support@futurscam.com
- 📚 Documentation : https://docs.futurscam.com
- 🐛 Issues : https://github.com/futurscam/api/issues

---

**Version** : 1.0.0  
**Dernière mise à jour** : 14 janvier 2026  
**Auteurs** : FuturScam Development Team
