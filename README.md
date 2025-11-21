# FuturScam API

A FastAPI-based REST API for RFP (Request for Proposal) management with integrated skill extraction using skillNer.

## Overview

This API provides two main endpoints:
- **`/mongodb`** - Full CRUD operations for RFP documents stored in MongoDB
- **`/skillboy`** - AI-powered skill extraction from job descriptions and text

## Installation

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (connection string required)

### Setup

1. **Clone/Download the repository**
   ```
   cd FuturScamFront
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```
   
   Then download spaCy model:
   ```
   python -m spacy download en_core_web_sm
   ```

3. **Configure credentials**
   
   Edit `params.py` and update MongoDB connection:
   ```python
   MONGO_URI = "mongodb+srv://your_username:your_password@your_cluster.mongodb.net/"
   DB_NAME = "FuturScam"
   COLLECTION_NAME = "RFP"
   ```

## Running the API

### Development Mode (with auto-reload)
```bash
uvicorn main:app --reload
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

Access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Health Check
```
GET /health
```
Returns API status.

**Response:**
```json
{
  "status": "ok",
  "message": "FuturScam API is running"
}
```

### /mongodb - RFP Management

#### Get All RFPs
```
GET /mongodb
```

**Response:**
```json
{
  "count": 5,
  "data": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "role": "Senior Data Engineer",
      "company_name": "TechCorp",
      "company_city": "Paris",
      "job_description": "...",
      "skills": [
        {"name": "Python", "level": "Expert"},
        {"name": "Spark", "level": "Advanced"}
      ],
      "languages": [
        {"name": "English", "level": "Fluent"}
      ]
    }
  ]
}
```

#### Get Single RFP
```
GET /mongodb/{doc_id}
```

**Parameters:**
- `doc_id` (path): MongoDB document ID

**Response:** Single RFP document

#### Create New RFP
```
POST /mongodb
Content-Type: application/json

{
  "role": "Senior Data Engineer",
  "company_name": "TechCorp",
  "company_city": "Paris",
  "job_description": "Looking for a skilled data engineer...",
  "skills": [
    {"name": "Python", "level": "Expert"},
    {"name": "Spark", "level": "Advanced"}
  ],
  "languages": [
    {"name": "English", "level": "Fluent"}
  ]
}
```

**Response:**
```json
{
  "message": "RFP created successfully",
  "id": "507f1f77bcf86cd799439011"
}
```

#### Update RFP
```
PUT /mongodb/{doc_id}
Content-Type: application/json

{
  "role": "Principal Data Engineer",
  "skills": [
    {"name": "Python", "level": "Expert"},
    {"name": "Kubernetes", "level": "Advanced"}
  ]
}
```

**Response:**
```json
{
  "message": "RFP updated successfully",
  "modified_count": 1
}
```

#### Delete RFP
```
DELETE /mongodb/{doc_id}
```

**Response:**
```json
{
  "message": "RFP deleted successfully",
  "deleted_count": 1
}
```

### /skillboy - Skill Extraction

#### Extract Skills from Text
```
POST /skillboy
Content-Type: application/json

{
  "text": "We are looking for a Python developer with expertise in Django, FastAPI, and PostgreSQL. Experience with Docker and AWS is a plus. You should know SQL and have worked with REST APIs."
}
```

**Response:**
```json
{
  "skills": [
    "Python",
    "Django",
    "FastAPI",
    "PostgreSQL",
    "Docker",
    "AWS",
    "SQL",
    "REST APIs"
  ],
  "count": 8
}
```

#### Check Skill Extractor Status
```
GET /skillboy/health
```

**Response:**
```json
{
  "status": "ready",
  "message": "Skill extractor is ready"
}
```

## Example Usage

### Using curl

#### Get all RFPs
```bash
curl http://localhost:8000/mongodb
```

#### Create RFP
```bash
curl -X POST http://localhost:8000/mongodb \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Python Developer",
    "company_name": "TechCorp",
    "company_city": "Paris",
    "job_description": "We need a Python expert with Django experience",
    "skills": [{"name": "Python", "level": "Expert"}],
    "languages": [{"name": "English", "level": "Fluent"}]
  }'
```

#### Extract skills
```bash
curl -X POST http://localhost:8000/skillboy \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Python developer needed with Django, FastAPI, PostgreSQL, Docker, and AWS knowledge"
  }'
```

### Using Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Extract skills
response = requests.post(
    f"{BASE_URL}/skillboy",
    json={"text": "Looking for a Python expert with Kubernetes and Docker experience"}
)
print(response.json())

# Create RFP
rfp_data = {
    "role": "Senior Backend Engineer",
    "company_name": "StartupXYZ",
    "company_city": "Lyon",
    "job_description": "We need experienced backend engineers...",
    "skills": [
        {"name": "Python", "level": "Expert"},
        {"name": "FastAPI", "level": "Advanced"}
    ],
    "languages": [
        {"name": "English", "level": "Fluent"}
    ]
}
response = requests.post(f"{BASE_URL}/mongodb", json=rfp_data)
print(response.json())

# Get all RFPs
response = requests.get(f"{BASE_URL}/mongodb")
print(response.json())
```

## Skill Database

The API uses `skill_db_relax_25.json` containing 23,501 IT/Data/Cybersecurity/Programming skills including:

- **Programming Languages**: Python, Java, JavaScript, TypeScript, Go, Rust, C++, C#, Kotlin, PHP, Ruby, Swift
- **Frameworks**: Django, FastAPI, Flask, React, Vue, Angular, Spring, .NET Core
- **Databases**: PostgreSQL, MySQL, MongoDB, Redis, Cassandra, Oracle, SQL Server
- **Cloud/DevOps**: AWS, Azure, GCP, Kubernetes, Docker, Terraform, Ansible, CloudFormation
- **Data/ML**: Spark, Kafka, Airflow, TensorFlow, PyTorch, scikit-learn, Pandas, NumPy
- **Cybersecurity**: Penetration Testing, SIEM, OAuth, SSL/TLS, Encryption, Network Security
- **Protocols/Standards**: REST APIs, GraphQL, gRPC, SOAP, MQTT, WebSockets

To update the skill database, edit `skill_db_relax_25.json` directly or use the `filter_skills.py` utility script.

## Architecture

```
main.py              <- FastAPI application (endpoints & logic)
params.py            <- Configuration (MongoDB credentials)
test.py              <- Skill extraction utilities (load_skill_terms, extract_skills)
skill_db_relax_25.json  <- Curated skills database (23,501 skills)
requirements.txt     <- Python dependencies
```

## Error Handling

The API returns appropriate HTTP status codes:

| Code | Scenario |
|------|----------|
| 200  | Success |
| 400  | Bad request (invalid data, empty text, malformed ID) |
| 404  | Document not found |
| 500  | Server error |
| 503  | Skill extractor not loaded |

All error responses include a `detail` field explaining the issue:
```json
{
  "detail": "Text field cannot be empty"
}
```

## Performance Notes

- **Skill extraction** uses skillNer with spaCy, optimized for CPU-only environments
- **First request** may be slower as the model loads into memory
- **Recommended**: Use the `/skillboy/health` endpoint to ensure the extractor is ready before sending extraction requests

## Files to Delete

If migrating from the old Streamlit application, remove:
- `front.py` - Old Streamlit UI (replaced by API)
- `test_del.py` - Testing utility (obsolete)
- `logo.png` - Frontend asset (no longer needed)

## Development

### Running Tests
```bash
pytest tests/
```

### Modifying Endpoints
Edit `main.py` directly. The API will auto-reload in development mode.

### Adding New Skills
Add entries to `skill_db_relax_25.json` using this format:
```json
{
  "skill_id": {
    "skill_name": "Kubernetes",
    "skill_type": "DevOps",
    "skill_len": 10,
    "high_surface_forms": ["kubernetes", "k8s"],
    "low_surface_forms": [],
    "match_on_tokens": true
  }
}
```

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Verify MongoDB connection in `params.py`
3. Ensure `skill_db_relax_25.json` exists
4. Verify spaCy model is installed: `python -m spacy download en_core_web_sm`

## License

Internal Use Only
