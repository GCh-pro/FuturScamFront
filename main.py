from fastapi import FastAPI, HTTPException, File, Form, UploadFile
from pydantic import BaseModel
from pymongo import MongoClient
from bson.objectid import ObjectId
from typing import List, Optional
import json
import asyncio
from functools import lru_cache
import os
import tempfile

from params import MONGO_URI, DB_NAME, COLLECTION_NAME
from test import load_skill_terms, create_extractor, extract_skills
from mail_sender import MailSender

# Initialize FastAPI app
app = FastAPI(
    title="FuturScam API",
    description="API for MongoDB management and skill extraction",
    version="1.0.0"
)

# MongoDB connection
def get_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]

def get_users_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db["Users"]

def get_staging_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db["StagingRFP"]

# Load skill extractor once at startup
skill_terms = None
extractor = None

@app.on_event("startup")
def startup():
    global skill_terms, extractor
    try:
        skill_terms = load_skill_terms("skill_db_optimized_20.json")
        extractor = create_extractor(skill_terms)
        print("✅ Skill extractor loaded successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not load skill extractor: {e}")

# ========================
# DATA MODELS
# ========================

class DailyRate(BaseModel):
    currency: str = "€"
    min: Optional[float] = None
    max: Optional[float] = None

class Conditions(BaseModel):
    dailyRate: DailyRate = DailyRate()
    fixedMargin: float = 0.0
    fromAt: str
    toAt: str
    startImmediately: bool = False
    occupation: str = ""

class Company(BaseModel):
    city: str
    name: str
    country: str = ""
    street: str = ""
    zipcode: str = ""
    region: Optional[str] = None

class Skill(BaseModel):
    name: str
    seniority: Optional[str] = ""

class Language(BaseModel):
    language: str
    level: Optional[str] = ""

class JobDocument(BaseModel):
    company: Company
    conditions: Conditions
    serviceProvider: Optional[str] = ""
    deadlineAt: str
    publishedAt: str
    metadata: Optional[dict] = None
    job_url: Optional[str] = None
    remoteOption: Optional[str] = None
    seniority: Optional[str] = None
    job_id: str
    job_desc: str
    roleTitle: str
    isActive: bool = True
    skills: Optional[List[Skill]] = []
    languages: Optional[List[Language]] = []

class JobUpdate(BaseModel):
    company: Optional[Company] = None
    conditions: Optional[Conditions] = None
    serviceProvider: Optional[str] = None
    deadlineAt: Optional[str] = None
    publishedAt: Optional[str] = None
    metadata: Optional[dict] = None
    job_url: Optional[str] = None
    remoteOption: Optional[str] = None
    seniority: Optional[str] = None
    job_id: Optional[str] = None
    job_desc: Optional[str] = None
    roleTitle: Optional[str] = None
    isActive: Optional[bool] = None
    skills: Optional[List[Skill]] = None
    languages: Optional[List[Language]] = None

class SkillExtractionRequest(BaseModel):
    text: str

class SkillExtractionResponse(BaseModel):
    skills: List[str]
    languages: List[str]
    skills_count: int
    languages_count: int

class User(BaseModel):
    company: str
    mail: str
    name: str
    role: str
    password: str
    id: str

class UserUpdate(BaseModel):
    company: Optional[str] = None
    mail: Optional[str]
    name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    id: Optional[str] = None

# ========================
# /MONGODB ENDPOINT
# ========================

@app.get("/mongodb")
def get_all_jobs():
    """Get all job documents from MongoDB"""
    try:
        collection = get_collection()
        docs = list(collection.find())
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return {"count": len(docs), "data": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mongodb/{job_id}")
def get_job(job_id: str):
    """Get a specific job document by job_id"""
    try:
        collection = get_collection()
        doc = collection.find_one({"job_id": job_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        doc["_id"] = str(doc["_id"])
        return doc
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/mongodb")
def create_job(job: JobDocument):
    """Create a new job document"""
    try:
        collection = get_collection()
        doc = job.model_dump()
        result = collection.insert_one(doc)
        return {
            "message": "Job posted successfully",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/mongodb/{job_id}")
def update_job(job_id: str, job: JobUpdate):
    """Update an existing job document by job_id"""
    try:
        collection = get_collection()
        update_data = job.model_dump(exclude_unset=True, exclude_none=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = collection.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "message": "Job updated successfully",
            "modified_count": result.modified_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/mongodb/{job_id}")
def delete_job(job_id: str):
    """Delete a job document by job_id"""
    try:
        collection = get_collection()
        result = collection.delete_one({"job_id": job_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "message": "Job deleted successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========================
# /STAGING ENDPOINT
# ========================

@app.get("/staging")
def get_all_staging_jobs():
    """Get all staging job documents from MongoDB"""
    try:
        collection = get_staging_collection()
        docs = list(collection.find())
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return {"count": len(docs), "data": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/staging/{job_id}")
def get_staging_job(job_id: str):
    """Get a specific staging job document by job_id"""
    try:
        collection = get_staging_collection()
        doc = collection.find_one({"job_id": job_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        doc["_id"] = str(doc["_id"])
        return doc
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/staging")
def create_staging_job(job: JobDocument):
    """Create a new staging job document"""
    try:
        collection = get_staging_collection()
        doc = job.model_dump()
        result = collection.insert_one(doc)
        return {
            "message": "Staging job posted successfully",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/staging/{job_id}")
def update_staging_job(job_id: str, job: JobUpdate):
    """Update an existing staging job document by job_id"""
    try:
        collection = get_staging_collection()
        update_data = job.model_dump(exclude_unset=True, exclude_none=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = collection.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "message": "Staging job updated successfully",
            "modified_count": result.modified_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/staging/{job_id}")
def delete_staging_job(job_id: str):
    """Delete a staging job document by job_id"""
    try:
        collection = get_staging_collection()
        result = collection.delete_one({"job_id": job_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "message": "Staging job deleted successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========================
# /USERS ENDPOINT
# ========================

@app.get("/users")
def get_all_users():
    """Get all user documents from MongoDB"""
    try:
        collection = get_users_collection()
        docs = list(collection.find())
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return {"count": len(docs), "data": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}")
def get_user(user_id: str):
    """Get a specific user document by id"""
    try:
        collection = get_users_collection()
        doc = collection.find_one({"id": user_id})
        if not doc:
            raise HTTPException(status_code=404, detail="User not found")
        doc["_id"] = str(doc["_id"])
        return doc
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/users")
def create_user(user: User):
    """Create a new user document"""
    try:
        collection = get_users_collection()
        
        # Check if user with this id already exists
        existing_user = collection.find_one({"id": user.id})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this id already exists")
        
        doc = user.model_dump()
        result = collection.insert_one(doc)
        return {
            "message": "User created successfully",
            "id": str(result.inserted_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/users/{user_id}")
def update_user(user_id: str, user: UserUpdate):
    """Update an existing user document by id"""
    try:
        collection = get_users_collection()
        update_data = user.model_dump(exclude_unset=True, exclude_none=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "message": "User updated successfully",
            "modified_count": result.modified_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    """Delete a user document by id"""
    try:
        collection = get_users_collection()
        result = collection.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "message": "User deleted successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========================
# /SKILLBOY ENDPOINT
# ========================

@app.post("/skillboy")
async def extract_skills_from_text(request: SkillExtractionRequest) -> SkillExtractionResponse:
    """Extract skills from text using the skill extractor model (timeout: 120 seconds)"""
    try:
        if not extractor:
            raise HTTPException(
                status_code=503,
                detail="Skill extractor not loaded. Make sure skill_db_relax_25.json exists."
            )
        
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text field cannot be empty")
        
        # Run extraction with 120 second timeout
        try:
            skills = await asyncio.wait_for(
                asyncio.to_thread(extract_skills, request.text, extractor),
                timeout=120.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Skill extraction timed out after 120 seconds. Text may be too long or complex."
            )
        
        # Separate languages from skills
        languages = []
        skills_only = []
        
        # Handle empty results safely
        if not skills:
            return SkillExtractionResponse(
                skills=[],
                languages=[],
                skills_count=0,
                languages_count=0
            )
        
        for skill in skills:
            if skill.lower().endswith("language"):
                languages.append(skill)
            else:
                skills_only.append(skill)
        
        return SkillExtractionResponse(
            skills=skills_only,
            languages=languages,
            skills_count=len(skills_only),
            languages_count=len(languages)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/skillboy/health")
def skillboy_health():
    """Check if skill extractor is loaded"""
    return {
        "status": "ready" if extractor else "not_loaded",
        "message": "Skill extractor is ready" if extractor else "Skill extractor not loaded"
    }

# ========================
# MAIL ENDPOINT
# ========================

# Initialize mail sender (lazy loading on first use)
mail_sender_instance = None

def get_mail_sender() -> MailSender:
    """Get or initialize the mail sender with application authentication."""
    global mail_sender_instance
    
    if mail_sender_instance is None:
        from params import AZURE_CLIENT, AZURE_URI, AZURE_SECRET, AZURE_MAILBOX
        scopes = ["https://graph.microsoft.com/.default"]
        mail_sender_instance = MailSender(
            client_id=AZURE_CLIENT,
            authority=AZURE_URI,
            client_secret=AZURE_SECRET,
            mailbox_email=AZURE_MAILBOX,
            scopes=scopes
        )
        mail_sender_instance.authenticate()
    
    return mail_sender_instance

@app.post("/mail")
async def send_email(
    to_addresses: str = Form(..., description="Comma-separated list of recipient email addresses"),
    subject: str = Form(..., description="Email subject"),
    body: str = Form(..., description="Email body (HTML or plain text)"),
    cc_addresses: Optional[str] = Form(None, description="Comma-separated list of CC addresses"),
    bcc_addresses: Optional[str] = Form(None, description="Comma-separated list of BCC addresses"),
    is_html: bool = Form(True, description="Whether body is HTML (default True)"),
    attachments: Optional[List[UploadFile]] = File(None, description="Files to attach (PDF, PNG, JPEG, etc.)")
) -> dict:
    """
    Send an email with optional attachments.
    
    Parameters:
    - to_addresses: Comma-separated email addresses (required)
    - subject: Email subject (required)
    - body: Email body content (required)
    - cc_addresses: Comma-separated CC addresses (optional)
    - bcc_addresses: Comma-separated BCC addresses (optional)
    - is_html: Whether body is HTML formatted (optional, default True)
    - attachments: Files to attach (optional, supports PDF, PNG, JPEG, etc.)
    
    Returns:
    - JSON response with status and message
    """
    try:
        # Parse email addresses
        to_list = [addr.strip() for addr in to_addresses.split(",") if addr.strip()]
        if not to_list:
            raise HTTPException(status_code=400, detail="At least one recipient email is required")
        
        cc_list = [addr.strip() for addr in cc_addresses.split(",") if addr.strip()] if cc_addresses else None
        bcc_list = [addr.strip() for addr in bcc_addresses.split(",") if addr.strip()] if bcc_addresses else None
        
        # Save uploaded files to temporary location
        temp_files = []
        try:
            if attachments:
                for file in attachments:
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                        content = await file.read()
                        tmp_file.write(content)
                        temp_files.append(tmp_file.name)
            
            # Get mail sender and send email
            sender = get_mail_sender()
            success = sender.send_email(
                to_addresses=to_list,
                subject=subject,
                body=body,
                attachments=temp_files if temp_files else None,
                cc_addresses=cc_list,
                bcc_addresses=bcc_list,
                is_html=is_html
            )
            
            if success:
                return {
                    "status": "success",
                    "message": f"Email sent successfully to {', '.join(to_list)}",
                    "recipients": {
                        "to": to_list,
                        "cc": cc_list,
                        "bcc": bcc_list
                    },
                    "attachments_count": len(temp_files)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to send email")
        
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"[WARN] Error deleting temp file {temp_file}: {e}")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

# ========================
# HEALTH CHECK
# ========================

@app.get("/health")
def health_check():
    """API health check"""
    return {
        "status": "ok",
        "message": "FuturScam API is running"
    }

# ========================
# ROOT ENDPOINT
# ========================

@app.get("/")
def root():
    """API documentation"""
    return {
        "name": "FuturScam API",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health - API health check",
            "mail": "POST /mail - Send email with attachments",
            "mongodb": {
                "get_all": "GET /mongodb - Get all RFPs",
                "get_one": "GET /mongodb/{doc_id} - Get specific RFP",
                "create": "POST /mongodb - Create new RFP",
                "update": "PUT /mongodb/{doc_id} - Update RFP",
                "delete": "DELETE /mongodb/{doc_id} - Delete RFP"
            },
            "skillboy": {
                "extract": "POST /skillboy - Extract skills from text",
                "health": "GET /skillboy/health - Check extractor status"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=120)
