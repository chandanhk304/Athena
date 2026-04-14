"""
Athena Core — Centralized Configuration
Loads all cloud service credentials from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Neon Postgres (shared with Simulator) ──────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")

# ─── Neo4j Aura ─────────────────────────────────────────────
NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USER = os.environ.get("NEO4J_USER")  # Instance ID for Aura free tier
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

# ─── Pinecone ───────────────────────────────────────────────
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "athena-vectors")
PINECONE_EMBED_MODEL = "multilingual-e5-large"  # 1024-dim, free via Pinecone Inference
PINECONE_EMBED_DIM = 1024

# ─── Groq (for LLM tasks in agent phase) ────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ─── Simulator ──────────────────────────────────────────────
SIMULATOR_API_URL = os.environ.get("SIMULATOR_API_URL", "http://localhost:8000/api/v1")

# ─── Athena Core ────────────────────────────────────────────
ATHENA_HOST = "0.0.0.0"
ATHENA_PORT = 8001
