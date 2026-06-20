"""
llm_client.py

A thin abstraction layer over LLM providers so the RAG pipeline isn't locked
to one vendor. Set LLM_PROVIDER in your .env file to switch between them.

Supported providers:
  - "openai"     -> OpenAI Chat Completions API
  - "groq"       -> Groq's OpenAI-compatible API (fast, generous free tier)
  - "anthropic"  -> Anthropic Messages API (Claude)
  - "none"       -> Offline fallback: returns the best-matching retrieved
                     answer directly, no external API call. Useful for
                     demos, testing, or running without an API key.

To add a new provider, implement a `_call_<provider>` method following the
same signature and register it in PROVIDER_DISPATCH.
"""

import os

SYSTEM_PROMPT = (
    "You are a helpful healthcare benefits assistant. Answer the user's "
    "question using ONLY the information provided in the context below. "
    "If the context does not contain enough information to answer "
    "confidently, say so clearly instead of guessing. Keep answers concise "
    "and in plain language. Do not provide medical diagnoses or treatment "
    "advice; this assistant covers benefits, claims, and plan information "
    "only."
)


class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "none").lower()

    def generate_answer(self, question: str, context: str) -> str:
        if not context.strip():
            return (
                "I couldn't find anything in the knowledge base relevant "
                "to that question. Could you rephrase it or ask about "
                "claims, prescriptions, benefits, telehealth, or account "
                "access?"
            )

        dispatch = {
            "openai": self._call_openai,
            "groq": self._call_groq,
            "anthropic": self._call_anthropic,
            "none": self._call_offline_fallback,
        }
        handler = dispatch.get(self.provider, self._call_offline_fallback)
        return handler(question, context)

    # ------------------------------------------------------------------
    # Offline fallback — no API key required. Useful for local demos.
    # ------------------------------------------------------------------
    def _call_offline_fallback(self, question: str, context: str) -> str:
        return (
            "[Offline mode — no LLM_PROVIDER configured]\n\n"
            "Here is the most relevant information I found:\n\n"
            f"{context}\n\n"
            "Set LLM_PROVIDER and an API key in your .env file to get a "
            "natural-language answer generated from this context instead."
        )

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    def _call_openai(self, question: str, context: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
            temperature=0.2,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    # Groq (OpenAI-compatible API, fast inference, free tier available)
    # ------------------------------------------------------------------
    def _call_groq(self, question: str, context: str) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
            temperature=0.2,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------
    def _call_anthropic(self, question: str, context: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                }
            ],
        )
        return response.content[0].text.strip()
