"""
rag_engine.py

Core Retrieval-Augmented Generation logic.

Pipeline:
  1. Load the knowledge base (healthcare FAQ documents).
  2. Embed every document using a Hugging Face sentence-transformer model.
  3. Build a FAISS vector index over those embeddings for fast similarity search.
  4. At query time: embed the user's question, retrieve the top-k most similar
     documents, and pass them as grounding context to the LLM.

This keeps the LLM's answers grounded in the actual knowledge base instead of
relying purely on the model's parametric memory, which reduces hallucination
and lets you cite where an answer came from.
"""

import json
import os
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DATA_PATH = Path(__file__).parent / "data" / "healthcare_faq.json"

# A small, fast embedding model. Good enough quality for a FAQ-sized
# knowledge base and cheap enough to run on CPU without a GPU.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class RAGEngine:
    def __init__(self, data_path: Path = DATA_PATH, top_k: int = 3):
        self.top_k = top_k
        self.documents = self._load_documents(data_path)
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.index, self.embeddings = self._build_index()

    @staticmethod
    def _load_documents(path: Path):
        with open(path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        # Concatenate question + answer so retrieval matches on both the
        # phrasing of the question and the content of the answer.
        for doc in docs:
            doc["_text"] = f"{doc['question']} {doc['answer']}"
        return docs

    def _build_index(self):
        texts = [doc["_text"] for doc in self.documents]
        embeddings = self.model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True
        )
        dimension = embeddings.shape[1]

        # Inner product over normalized vectors == cosine similarity.
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings.astype("float32"))
        return index, embeddings

    def retrieve(self, query: str):
        """Return the top-k most relevant documents for a query."""
        query_vec = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")

        scores, indices = self.index.search(query_vec, self.top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            doc = self.documents[idx]
            results.append(
                {
                    "id": doc["id"],
                    "category": doc["category"],
                    "question": doc["question"],
                    "answer": doc["answer"],
                    "score": float(score),
                }
            )
        return results

    def build_context_block(self, retrieved_docs):
        """Format retrieved docs into a context block for the LLM prompt."""
        lines = []
        for doc in retrieved_docs:
            lines.append(
                f"[Source: {doc['category']} | {doc['id']}]\n"
                f"Q: {doc['question']}\nA: {doc['answer']}"
            )
        return "\n\n".join(lines)
