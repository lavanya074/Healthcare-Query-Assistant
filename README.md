# Healthcare Query Assistant (RAG-based LLM Chatbot)

A Retrieval-Augmented Generation chatbot that answers healthcare benefits,
claims, and prescription questions using a knowledge base + an LLM —
instead of letting the LLM guess from memory alone.

Built to demonstrate: **LLMs & RAG, REST APIs, React.js, Python backend
development, SQL/NoSQL persistence, and cloud deployment.**

---

## Why RAG, and why this matters

A plain LLM chatbot answers from what it learned during training, which
means it can confidently make things up ("hallucinate") about specifics
like deductible amounts or refill processes it was never actually told
about. **Retrieval-Augmented Generation** fixes this by:

1. Storing your real knowledge base (FAQs, policy docs, etc.) as vector
   embeddings.
2. At query time, retrieving the most relevant chunks for the user's
   question.
3. Handing those chunks to the LLM as context and instructing it to
   answer **only** from that context.

The result: answers are grounded in your actual content, and you can show
*which* source documents informed each answer.

---

## Architecture

```
┌─────────────────┐      REST (JSON over HTTP)      ┌──────────────────────┐
│   React frontend │ ───────────────────────────────▶ │   Flask backend API  │
│  (chat UI)       │ ◀─────────────────────────────── │   /api/chat          │
└─────────────────┘                                   └──────────┬───────────┘
                                                                  │
                                  ┌───────────────────────────────┼───────────────────────┐
                                  ▼                               ▼                       ▼
                          ┌───────────────┐              ┌────────────────┐     ┌──────────────────┐
                          │  RAG Engine   │              │   LLM Client    │     │  SQLite database  │
                          │ sentence-     │              │ OpenAI / Groq / │     │  (chat sessions &  │
                          │ transformers  │              │ Anthropic /     │     │   message history) │
                          │ + FAISS index │              │ offline mode    │     └──────────────────┘
                          └───────────────┘              └────────────────┘
```

**Flow per message:**
`user types question → React POSTs to /api/chat → Flask embeds the query
→ FAISS retrieves top-3 matching FAQ entries → those are inserted into the
LLM prompt as context → LLM generates a grounded answer → response +
source citations returned to React → conversation saved to SQLite`

---

## Tech stack

| Layer            | Technology                                              |
|-------------------|----------------------------------------------------------|
| Frontend          | React.js (functional components, hooks)                 |
| Backend           | Python, Flask, REST API                                  |
| Embeddings        | Hugging Face `sentence-transformers` (`all-MiniLM-L6-v2`)|
| Vector search      | FAISS                                                    |
| LLM               | Pluggable: OpenAI, Groq, or Anthropic (swap via `.env`)  |
| Database          | SQLite (drop-in swappable for MySQL / MongoDB — see below) |
| Deployment        | Render/Railway (backend) + Vercel/Netlify (frontend)     |

---

## Project structure

```
healthcare-rag-chatbot/
├── backend/
│   ├── app.py            # Flask REST API
│   ├── rag_engine.py     # Embedding + FAISS retrieval
│   ├── llm_client.py     # Multi-provider LLM abstraction
│   ├── database.py       # SQLite session/chat history
│   ├── data/
│   │   └── healthcare_faq.json   # Sample knowledge base (15 FAQs)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   ├── index.js / index.css / styles.css
    │   └── components/
    │       ├── Sidebar.jsx
    │       ├── MessageBubble.jsx
    │       └── ChatInput.jsx
    ├── public/index.html
    ├── package.json
    └── .env.example
```

---

## Setup & local run

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set LLM_PROVIDER and the matching API key.
# Leave LLM_PROVIDER=none to run without any API key — it will return
# the raw retrieved FAQ content instead of an LLM-generated answer,
# which is enough to verify the retrieval pipeline works end to end.

python app.py
```

The first run downloads the embedding model from Hugging Face (~90MB),
so it needs an internet connection once. The Flask server starts on
`http://localhost:5000`.

Quick check:
```bash
curl http://localhost:5000/api/health
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env       # defaults to http://localhost:5000
npm start
```

Opens at `http://localhost:3000`.

---

## Switching LLM providers

Set `LLM_PROVIDER` in `backend/.env` to one of `openai`, `groq`,
`anthropic`, or `none`. Add the matching API key on the line below it.
**Groq** is a good first choice if you want a free tier to test with.

---

## Swapping SQLite for MySQL or MongoDB

The project ships with SQLite so it runs with zero external setup, but
`database.py` is intentionally minimal so it's easy to swap:

- **MySQL**: replace the `sqlite3` connection in `database.py` with
  `mysql-connector-python` or `PyMySQL`. The `CREATE TABLE` statements are
  standard SQL and need no changes.
- **MongoDB**: replace each table with a collection (`sessions`,
  `messages`) and each row with a document. Use `session_id` as the
  partition/lookup key, same as the SQL version.

---

## Deployment

**Backend (Render — free tier works for a demo):**
1. Push this repo to GitHub.
2. On Render: New → Web Service → connect the repo, root directory
   `backend/`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app` (add `gunicorn` to requirements.txt
   for production; the built-in Flask dev server is fine for local use
   only).
5. Add your `.env` values under Render's Environment Variables tab.

**Frontend (Vercel):**
1. Import the repo on Vercel, set root directory to `frontend/`.
2. Set the environment variable `REACT_APP_API_BASE_URL` to your deployed
   Render backend URL.
3. Deploy — Vercel auto-detects the Create React App build.

---

## API reference

| Method | Endpoint              | Description                              |
|--------|------------------------|-------------------------------------------|
| GET    | `/api/health`           | Liveness check + indexed document count   |
| POST   | `/api/session`          | Create a new chat session                 |
| POST   | `/api/chat`             | Send a message, get a grounded answer      |
| GET    | `/api/history/<id>`     | Retrieve full history for a session        |

`POST /api/chat` request body:
```json
{ "message": "How do I refill a prescription?", "session_id": "optional" }
```

Response:
```json
{
  "session_id": "…",
  "answer": "…",
  "sources": [
    { "id": "faq-004", "category": "Prescriptions", "question": "…", "score": 0.83 }
  ]
}
```

---
<img width="1912" height="905" alt="image" src="https://github.com/user-attachments/assets/e8672b0a-663d-479a-932e-3a1dceeeb1bc" />


## Notes on the knowledge base

`backend/data/healthcare_faq.json` ships with 15 sample FAQs across six
categories (claims, prescriptions, benefits, telehealth, wellness,
account access) so the project runs out of the box. Swap in your own
documents by editing that file, or extend `rag_engine.py` to load from a
folder of PDFs/markdown files instead of a single JSON file for a larger
knowledge base.

## Disclaimer

This is a benefits/claims information assistant, not a medical advice
tool. The system prompt in `llm_client.py` explicitly instructs the model
to avoid diagnoses or treatment recommendations.
