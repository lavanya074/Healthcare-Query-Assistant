"""
app.py

Flask REST API for the Healthcare Query Assistant.

Endpoints:
  GET  /api/health          -> liveness check
  POST /api/session         -> create a new chat session
  POST /api/chat            -> send a message, get a RAG-grounded answer
  GET  /api/history/<id>    -> retrieve chat history for a session

Run locally:
  python app.py
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

import database
from llm_client import LLMClient
from rag_engine import RAGEngine

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow the React frontend (different origin in dev) to call this API.

# Loaded once at startup: building the FAISS index over ~15 docs is fast,
# but for a larger knowledge base you'd want to build and persist the index
# separately rather than rebuilding it on every server start.
rag_engine = RAGEngine(top_k=3)
llm_client = LLMClient()

database.init_db()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "documents_indexed": len(rag_engine.documents)})


@app.route("/api/session", methods=["POST"])
def create_session():
    session_id = database.create_session()
    return jsonify({"session_id": session_id})


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    session_id = payload.get("session_id")

    if not message:
        return jsonify({"error": "message is required"}), 400

    if not session_id or not database.session_exists(session_id):
        session_id = database.create_session()

    # 1. Retrieve relevant context from the knowledge base.
    retrieved_docs = rag_engine.retrieve(message)
    context = rag_engine.build_context_block(retrieved_docs)

    # 2. Generate a grounded answer using the configured LLM provider.
    answer = llm_client.generate_answer(message, context)

    # 3. Persist the turn for this session.
    database.save_message(session_id, "user", message)
    database.save_message(session_id, "assistant", answer)

    return jsonify(
        {
            "session_id": session_id,
            "answer": answer,
            "sources": [
                {
                    "id": doc["id"],
                    "category": doc["category"],
                    "question": doc["question"],
                    "score": round(doc["score"], 3),
                }
                for doc in retrieved_docs
            ],
        }
    )


@app.route("/api/history/<session_id>", methods=["GET"])
def history(session_id):
    if not database.session_exists(session_id):
        return jsonify({"error": "session not found"}), 404
    return jsonify({"session_id": session_id, "messages": database.get_history(session_id)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
