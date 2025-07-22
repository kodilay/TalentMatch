import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import json
import re

class SimilarityEngine:
    def __init__(self, transformer_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the sentence embedding model and prepare index structure.
        """
        self.embedder = SentenceTransformer(transformer_model)
        self.vector_index = None
        self.items = []
        self.vec_size = self.embedder.get_sentence_embedding_dimension()
        
    def build_index(self, documents: List[Dict]):
        """
        Encodes and indexes the given list of documents for similarity search.
        """
        self.items = documents
        content_list = [doc["text"] for doc in documents]
        encoded_vectors = self.embedder.encode(content_list)
        
        self.vector_index = faiss.IndexFlatL2(self.vec_size)
        self.vector_index.add(np.array(encoded_vectors).astype("float32"))

    def query_similar(self, input_text: str, top_k: int = 5) -> List[Dict]:
        """
        Finds top-k similar entries to the input text.
        """
        if self.vector_index is None:
            raise RuntimeError("Index is empty. Please run build_index first.")
        
        vector = self.embedder.encode([input_text])[0]
        scores, retrieved_ids = self.vector_index.search(
            np.array([vector]).astype("float32"), top_k
        )
        
        feedback = []
        for dist, idx in zip(scores[0], retrieved_ids[0]):
            if idx < len(self.items):
                entry = self.items[idx]
                score_pct = 100 * (1 - dist / 2)

                skill_gap = self._get_unmatched_skills(
                    input_text, entry.get("skills", [])
                )

                feedback.append({
                    "item_id": entry["id"],
                    "similarity_score": round(score_pct, 2),
                    "unmatched_skills": skill_gap,
                    "summary": self._craft_summary(score_pct, skill_gap)
                })
                
        return feedback

    def _get_unmatched_skills(self, text: str, available_skills: List[str]) -> List[str]:
        """
        Returns words in the input that are not in the candidate's skills list.
        """
        tokens = set(re.findall(r'\b\w+\b', text.lower()))
        normalized_skills = {skill.lower() for skill in available_skills}
        return [token for token in tokens if token not in normalized_skills]

    def _craft_summary(self, score: float, missing: List[str]) -> str:
        """
        Creates a brief explanation for the similarity score.
        """
        result = f"Match score: {score}%"
        if missing:
            result += f"\nMissing skillset: {', '.join(missing)}"
        return result

    def export_index(self, filepath: str):
        """
        Saves the index to a local file.
        """
        if self.vector_index:
            faiss.write_index(self.vector_index, filepath)

    def import_index(self, filepath: str):
        """
        Loads a pre-saved index from disk.
        """
        self.vector_index = faiss.read_index(filepath)