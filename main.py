from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson.objectid import ObjectId
from typing import List, Optional
import json

from params import MONGO_URI, DB_NAME, COLLECTION_NAME
from test import load_skill_terms, create_extractor, extract_skills

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

# Load skill extractor once at startup
skill_terms = None
extractor = None

@app.on_event("startup")
def startup():
    global skill_terms, extractor
    try:
        skill_terms = load_skill_terms("skill_db_relax_20.json")
        extractor = create_extractor(skill_terms)
        print("✅ Skill extractor loaded successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not load skill extractor: {e}")

# ========================
# DATA MODELS
# ========================

class SkillItem(BaseModel):
    name: str
    level: str = ""

class LanguageItem(BaseModel):
    name: str
    level: str = ""

class RFPDocument(BaseModel):
    role: str
    company_name: str
    company_city: str
    job_description: str
    skills: List[SkillItem] = []
    languages: List[LanguageItem] = []

class RFPUpdate(BaseModel):
    role: Optional[str] = None
    company_name: Optional[str] = None
    company_city: Optional[str] = None
    job_description: Optional[str] = None
    skills: Optional[List[SkillItem]] = None
    languages: Optional[List[LanguageItem]] = None

class SkillExtractionRequest(BaseModel):
    text: str

class SkillExtractionResponse(BaseModel):
    skills: List[str]
    count: int

# ========================
# /MONGODB ENDPOINT
# ========================

@app.get("/mongodb")
def get_all_rfps():
    """Get all RFP documents from MongoDB"""
    try:
        collection = get_collection()
        docs = list(collection.find())
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return {"count": len(docs), "data": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mongodb/{doc_id}")
def get_rfp(doc_id: str):
    """Get a specific RFP document by ID"""
    try:
        collection = get_collection()
        doc = collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        doc["_id"] = str(doc["_id"])
        return doc
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/mongodb")
def create_rfp(rfp: RFPDocument):
    """Create a new RFP document"""
    try:
        collection = get_collection()
        doc = {
            "role": rfp.role,
            "company_name": rfp.company_name,
            "company_city": rfp.company_city,
            "job_description": rfp.job_description,
            "skills": [s.dict() for s in rfp.skills],
            "languages": [l.dict() for l in rfp.languages]
        }
        result = collection.insert_one(doc)
        return {
            "message": "RFP created successfully",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/mongodb/{doc_id}")
def update_rfp(doc_id: str, rfp: RFPUpdate):
    """Update an existing RFP document"""
    try:
        collection = get_collection()
        update_data = {}
        
        if rfp.role is not None:
            update_data["role"] = rfp.role
        if rfp.company_name is not None:
            update_data["company_name"] = rfp.company_name
        if rfp.company_city is not None:
            update_data["company_city"] = rfp.company_city
        if rfp.job_description is not None:
            update_data["job_description"] = rfp.job_description
        if rfp.skills is not None:
            update_data["skills"] = [s.dict() for s in rfp.skills]
        if rfp.languages is not None:
            update_data["languages"] = [l.dict() for l in rfp.languages]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "message": "RFP updated successfully",
            "modified_count": result.modified_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/mongodb/{doc_id}")
def delete_rfp(doc_id: str):
    """Delete an RFP document"""
    try:
        collection = get_collection()
        result = collection.delete_one({"_id": ObjectId(doc_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "message": "RFP deleted successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========================
# /SKILLBOY ENDPOINT
# ========================

@app.post("/skillboy")
def extract_skills_from_text(request: SkillExtractionRequest) -> SkillExtractionResponse:
    """Extract skills from text using the skill extractor model"""
    try:
        if not extractor:
            raise HTTPException(
                status_code=503,
                detail="Skill extractor not loaded. Make sure skill_db_relax_20.json exists."
            )
        
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text field cannot be empty")
        
        skills = extract_skills(request.text, extractor)
        
        return SkillExtractionResponse(
            skills=skills,
            count=len(skills)
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
