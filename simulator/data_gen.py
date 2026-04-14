"""
LLM-Driven Data Generator — Groq-Only with Dual-Model Rotation
Uses llama-3.3-70b for structural generation (users, projects, epics)
Uses llama-3.1-8b-instant for high-volume batch generation (stories, comments)

Groq Free Tier Limits:
  llama-3.3-70b-versatile: 30 RPM, 1K RPD, 12K TPM, 100K TPD
  llama-3.1-8b-instant:    30 RPM, 14.4K RPD, 6K TPM, 500K TPD
"""
import os
import json
import time
import random
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Model tiers
MODEL_QUALITY = "llama-3.3-70b-versatile"   # Smarter, lower daily limits
MODEL_FAST = "llama-3.1-8b-instant"          # Faster, 14x higher daily limits

groq_client = None
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"[DataGen] Groq client init failed: {e}")


def _generate_with_groq(prompt: str, model: str = MODEL_FAST, max_tokens: int = 2048) -> str:
    """Call Groq API with automatic retry on rate limit (429)."""
    if not groq_client:
        return ""
    for attempt in range(3):
        try:
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.7,
                max_completion_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                wait = 2 ** attempt + random.uniform(0, 1)
                print(f"  [Rate Limit] Waiting {wait:.1f}s before retry {attempt+1}/3...")
                time.sleep(wait)
            else:
                print(f"  [Groq Error] {e}")
                return ""
    return ""


def llm_generate_json(prompt: str, schema_hints: str, model: str = MODEL_FAST) -> dict:
    """Uses Groq LLM to generate enterprise data and parses it as JSON."""
    full_prompt = f"""You are an enterprise simulation engine generating highly realistic Jira ticket data.
Do not use generic placeholder names like 'Test Ticket' or 'Fix Bug'. Use corporate jargon,
mention microservices down to the module level (e.g. payment-gateway-svc), reference real tech debt,
and include realistic human frustration if relevant.

Task:
{prompt}

Return ONLY a raw JSON object corresponding to this structure, no markdown, no backticks, no code blocks:
{schema_hints}"""

    raw_result = _generate_with_groq(full_prompt, model=model)
    if not raw_result:
        return {}

    try:
        raw_result = raw_result.strip()
        # Strip markdown code fences if present
        if raw_result.startswith("```json"):
            raw_result = raw_result[7:]
        if raw_result.startswith("```"):
            raw_result = raw_result[3:]
        if raw_result.endswith("```"):
            raw_result = raw_result[:-3]
        return json.loads(raw_result.strip())
    except json.JSONDecodeError as e:
        print(f"  [JSON Parse Error] {e}")
        return {}


# ─── Structural Generation (uses 70B for higher quality) ────────────────────

def generate_realistic_users(count: int = 20) -> list:
    prompt = (
        f"Generate {count} highly diverse software enterprise employees. "
        "Use realistic first/last names from varied ethnicities. "
        "Include corporate emails (e.g. j.doe@acme.com). "
        "Assign roles strictly from: DEV, QA, TECH_LEAD, PM, DESIGN, VP. "
        "Distribution: ~10 DEV, 3 QA, 2 TECH_LEAD, 2 PM, 2 DESIGN, 1 VP."
    )
    schema = '{"users": [{"name": "string", "email": "string", "role": "string"}]}'
    res = llm_generate_json(prompt, schema, model=MODEL_QUALITY)
    return res.get("users", [])


def generate_core_project() -> dict:
    prompt = (
        "Generate a realistic, large-scale software project for a Fortune 500 company. "
        "Come up with a creative Project Name (e.g. 'Project Phoenix'), "
        "a 3-4 letter uppercase Project Key, a brief description, "
        "and 3 major Epic initiatives each with title and description."
    )
    schema = '{"project_name": "string", "project_key": "string", "description": "string", "epics": [{"title": "string", "description": "string"}]}'
    return llm_generate_json(prompt, schema, model=MODEL_QUALITY)


# ─── High-Volume Batch Generation (uses 8B for speed + higher limits) ───────

def generate_realistic_stories_batch(epic_title: str, count: int = 10) -> list:
    prompt = (
        f"Write {count} highly detailed, realistic Jira Stories belonging to the epic '{epic_title}'. "
        "Include technical implementation notes, mention specific microservices, cloud tools, "
        "or infrastructure components. Be specific and vary the priorities. "
        "Use priorities from: LOW, MEDIUM, HIGH, CRITICAL. "
        "Use story points from: 1, 2, 3, 5, 8, 13."
    )
    schema = '{"stories": [{"title": "string", "description": "string", "story_points": 3, "priority": "MEDIUM"}]}'
    res = llm_generate_json(prompt, schema, model=MODEL_FAST)
    return res.get("stories", [])


def generate_realistic_comments_batch(story_title: str, count: int = 2) -> list:
    prompt = (
        f"Write {count} realistic, chronological Jira comments from engineers working on "
        f"the story '{story_title}'. The comments should track progress, mention bugs, "
        "ask for PR reviews, or discuss deployment issues. Sound like actual humans in a company."
    )
    schema = '{"comments": [{"body": "string"}]}'
    res = llm_generate_json(prompt, schema, model=MODEL_FAST)
    return res.get("comments", [])