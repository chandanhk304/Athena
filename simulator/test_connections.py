#!/usr/bin/env python3
"""
Cloud Service Connectivity Test
Run: python simulator/test_connections.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_neon_postgres():
    print("1. NEON POSTGRES")
    try:
        from sqlalchemy import create_engine, text
        url = os.environ.get("DATABASE_URL")
        if not url:
            print("   STATUS: SKIPPED - DATABASE_URL not set")
            return False
        print(f"   URL: {url[:60]}...")
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            print(f"   STATUS: ✅ CONNECTED")
            print(f"   Version: {result.fetchone()[0][:60]}")
            return True
    except Exception as e:
        print(f"   STATUS: ❌ FAILED - {e}")
        return False

def test_groq():
    print("2. GROQ API (Primary LLM for Simulator)")
    try:
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            print("   STATUS: SKIPPED - GROQ_API_KEY not set")
            return False
        client = Groq(api_key=key)
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say OK"}],
            model="llama-3.1-8b-instant", max_completion_tokens=5
        )
        print(f"   STATUS: ✅ CONNECTED (llama-3.1-8b-instant)")
        print(f"   Response: {resp.choices[0].message.content}")

        resp2 = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say OK"}],
            model="llama-3.3-70b-versatile", max_completion_tokens=5
        )
        print(f"   STATUS: ✅ CONNECTED (llama-3.3-70b-versatile)")
        print(f"   Response: {resp2.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"   STATUS: ❌ FAILED - {e}")
        return False

def test_neo4j():
    print("3. NEO4J AURA")
    try:
        from neo4j import GraphDatabase
        uri = os.environ.get("NEO4J_URI")
        user = os.environ.get("NEO4J_USER")
        pwd = os.environ.get("NEO4J_PASSWORD")
        if not uri:
            print("   STATUS: SKIPPED - NEO4J_URI not set")
            return False
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        driver.verify_connectivity()
        print(f"   STATUS: ✅ CONNECTED")
        driver.close()
        return True
    except Exception as e:
        print(f"   STATUS: ❌ FAILED - {e}")
        return False

def test_pinecone():
    print("4. PINECONE")
    try:
        from pinecone import Pinecone
        key = os.environ.get("PINECONE_API_KEY")
        if not key:
            print("   STATUS: SKIPPED - PINECONE_API_KEY not set")
            return False
        pc = Pinecone(api_key=key)
        indexes = pc.list_indexes()
        print(f"   STATUS: ✅ CONNECTED")
        print(f"   Indexes: {[i.name for i in indexes]}")
        return True
    except Exception as e:
        print(f"   STATUS: ❌ FAILED - {e}")
        return False

def test_gemini():
    """Optional: Gemini is used in Athena Core (later phases), not the Simulator."""
    print("5. GEMINI API (Optional — used in Athena Core, not Simulator)")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            print("   STATUS: SKIPPED - GEMINI_API_KEY not set")
            return True  # Not required for simulator
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key)
        resp = llm.invoke("Say OK")
        print(f"   STATUS: ✅ CONNECTED")
        print(f"   Response: {resp.content[:50]}")
        return True
    except Exception as e:
        print(f"   STATUS: ⚠️  UNAVAILABLE (not needed for simulator) - {str(e)[:80]}")
        return True  # Non-blocking for simulator phase

if __name__ == "__main__":
    print("=" * 55)
    print("  ATHENA — CLOUD SERVICE CONNECTIVITY TEST")
    print("=" * 55)
    print()

    results = {}
    results["Neon Postgres"] = test_neon_postgres(); print()
    results["Groq API"] = test_groq(); print()
    results["Neo4j Aura"] = test_neo4j(); print()
    results["Pinecone"] = test_pinecone(); print()
    results["Gemini (optional)"] = test_gemini(); print()

    print("=" * 55)
    print("  SUMMARY")
    print("=" * 55)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n  {passed}/{total} services ready.")
    print()

    # Only the first 4 are required for the simulator
    required = {k: v for k, v in results.items() if "optional" not in k.lower()}
    if all(required.values()):
        print("  🚀 All required services ready! Run:")
        print("     python -m simulator.timeline_sim")
        sys.exit(0)
    else:
        print("  ⚠️  Fix the failing services before running timeline_sim")
        sys.exit(1)
