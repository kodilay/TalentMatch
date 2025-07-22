from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import os

from document_processor import process_document
from cv_parser import parse_cv
from similarity_engine import SimilarityEngine
from database import Database
from notification_service import NotificationService
from fastapi.encoders import jsonable_encoder

app = FastAPI(
    title="TalentMatcher API",
    description="An API for parsing CVs and matching candidates with jobs.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = Database()
matcher = SimilarityEngine()
notifier = NotificationService()

# Data models
class Job(BaseModel):
    title: str
    description: str
    requirements: List[str]
    location: str
    company: str
    matching_parameters: Optional[dict] = None

class CandidateMatch(BaseModel):
    candidate_id: str
    match_percentage: float
    missing_skills: List[str]
    explanation: str

class MatchConfig(BaseModel):
    min_match_percentage: float = 70.0
    required_skills: List[str] = []
    preferred_skills: List[str] = []

@app.get("/")
async def welcome():
    return {"message": "Welcome to the TalentMatcher API"}

@app.post("/upload")
async def upload_cv_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are accepted")

    try:
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1]
        parsed_text = process_document(contents, ext)
        extracted = parse_cv(parsed_text)
        cv_id = str(db.store_cv(extracted.__dict__, contents, file.filename))

        return {
            "message": "CV uploaded and parsed successfully",
            "cv_id": cv_id,
            "parsed": jsonable_encoder(extracted)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/job")
async def post_job(job: Job):
    try:
        job_id = db.store_job_posting(job.dict())
        return {"message": "Job posted successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/match/{job_id}")
async def match(job_id: str):
    try:
        job = db.get_job_posting(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        candidates = db.get_all_candidates()
        matcher.build_index(candidates)
        result = matcher.query_similar(
            f"{job['title']} {job['description']} {' '.join(job['requirements'])}"
        )

        for match in result:
            db.store_match(job_id, match["candidate_id"], match)
            cv = db.get_cv(match["candidate_id"])
            if cv:
                notifier.notify_match(
                    cv.get("email"),
                    cv.get("phone"),
                    match
                )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/job/{job_id}/config")
async def update_config(job_id: str, config: MatchConfig):
    try:
        updated = db.update_match_parameters(job_id, config.dict())
        if not updated:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"message": "Matching config updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job/{job_id}/results")
async def get_matches(job_id: str):
    try:
        return db.get_matches_for_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)