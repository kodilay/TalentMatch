
from pymongo import MongoClient
from gridfs import GridFS
from typing import Dict, List, Optional
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class DBHandler:
    def __init__(self):
        """
        Initialize MongoDB connection and GridFS.
        """
        self.client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/"))
        self.db = self.client["talentmatch"]
        self.fs = GridFS(self.db)

        # Collections
        self.candidate_collection = self.db["candidates"]
        self.job_collection = self.db["job_postings"]
        self.match_collection = self.db["matches"]

    def save_cv(self, cv_info: Dict, file_bytes: bytes, file_name: str) -> str:
        """
        Save the CV file into GridFS and store metadata in the candidates collection.
        """
        content_type = "application/pdf" if file_name.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        # Save the file to GridFS
        gridfs_id = self.fs.put(
            file_bytes,
            filename=file_name,
            content_type=content_type
        )

        # Save metadata
        cv_info["file_id"] = gridfs_id
        cv_info["created_on"] = datetime.utcnow()
        result = self.candidate_collection.insert_one(cv_info)

        return str(result.inserted_id)

    def retrieve_cv(self, cv_id: str) -> Optional[Dict]:
        """
        Retrieve CV metadata and file content based on provided CV id.
        """
        cv_record = self.candidate_collection.find_one({"_id": cv_id})
        if cv_record and "file_id" in cv_record:
            file_record = self.fs.get(cv_record["file_id"])
            cv_record["file_content"] = file_record.read()
            return cv_record
        return None

    def save_job_posting(self, job_info: Dict) -> str:
        """
        Save the job posting information into the database.
        """
        job_info["created_on"] = datetime.utcnow()
        result = self.job_collection.insert_one(job_info)
        return str(result.inserted_id)

    def retrieve_job_posting(self, job_id: str) -> Optional[Dict]:
        """
        Retrieve a job posting from the database.
        """
        return self.job_collection.find_one({"_id": job_id})

    def save_match(self, job_id: str, candidate_id: str, match_details: Dict) -> str:
        """
        Save the match result into the database.
        """
        match_details.update({
            "job_id": job_id,
            "candidate_id": candidate_id,
            "created_on": datetime.utcnow()
        })
        result = self.match_collection.insert_one(match_details)
        return str(result.inserted_id)

    def retrieve_matches_for_job(self, job_id: str) -> List[Dict]:
        """
        Retrieve all match records for a specific job posting, sorted by match_percentage descending.
        """
        return list(self.match_collection.find({"job_id": job_id}).sort("match_percentage", -1))

    def fetch_all_candidates(self) -> List[Dict]:
        """
        Retrieve all candidate records from the database.
        """
        return list(self.candidate_collection.find())

    def fetch_all_job_postings(self) -> List[Dict]:
        """
        Retrieve all job postings from the database.
        """
        return list(self.job_collection.find())

    def modify_match_parameters(self, job_id: str, parameters: Dict) -> bool:
        """
        Update the matching parameters for a job posting.
        """
        result = self.job_collection.update_one(
            {"_id": job_id},
            {"$set": {"matching_parameters": parameters}}
        )
        return result.modified_count > 0
