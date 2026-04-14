"""
Chaos Engine — Injects realistic enterprise failures into the simulator.
Uses Groq LLM to generate contextual failure comments.
"""
import random
import requests
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
from .data_gen import llm_generate_json

SIM_API = os.environ.get("SIMULATOR_API_URL", "http://localhost:8000/api/v1")

def get_stories():
    try:
        r = requests.get(f"{SIM_API}/stories?limit=500", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[Chaos] Failed to fetch stories: {e}")
    return []

def get_users():
    try:
        r = requests.get(f"{SIM_API}/users", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def generate_chaos_comment(context: str) -> str:
    """Uses Groq LLM to write a frantic, realistic comment about the failure."""
    prompt = (
        f"Write a brief, highly realistic Jira comment from an engineer experiencing this emergency: "
        f"{context}. Be technical. Mention specific systems (auth, db, gateway)."
    )
    schema = '{"body": "string"}'
    res = llm_generate_json(prompt, schema)  # Uses default MODEL_FAST
    return res.get("body", "CRITICAL ERROR: System failure detected. Investigating immediately.")

def inject_ticket_blocker():
    """Fault Pattern 1: Marks a CRITICAL or HIGH ticket as BLOCKED."""
    print("\n[Chaos] Attempting to inject TICKET_BLOCKER...")
    stories = get_stories()

    # HLD v0.4.0: statuses are OPEN/IN_PROGRESS/BLOCKED/CLOSED
    candidates = [s for s in stories if s.get("priority") in ("CRITICAL", "HIGH") and s.get("status") not in ("CLOSED", "BLOCKED")]
    if len(candidates) < 2:
        print("[Chaos] Not enough eligible stories. Skipping.")
        return

    target = random.choice(candidates)
    blocker = random.choice([s for s in stories if s["id"] != target["id"]])

    try:
        requests.patch(f"{SIM_API}/stories/{target['id']}", json={"status": "BLOCKED"}, timeout=5)

        comment_text = generate_chaos_comment(
            f"Ticket {target.get('key', 'UNKNOWN')} is blocked because "
            f"{blocker.get('key', 'UNKNOWN')} broke the build API."
        )
        comment_payload = {
            "id": f"CMT-CHAOS-{os.urandom(4).hex()}",
            "story_id": target["id"],
            "author_id": target.get("assignee_id") or target.get("reporter_id", "SYSTEM"),
            "body": f"BLOCKER: {comment_text}"
        }
        requests.post(f"{SIM_API}/comments", json=comment_payload, timeout=5)

        print(f"[Chaos] SUCCESS: {target.get('key')} is now BLOCKED by {blocker.get('key')}")
    except Exception as e:
        print(f"[Chaos Error] {e}")

def inject_developer_overload():
    """Fault Pattern 2: Assigns >5 CRITICAL tasks to a single developer."""
    print("\n[Chaos] Attempting to inject DEVELOPER_OVERLOAD...")
    users = [u for u in get_users() if u.get("role") in ("DEV", "TECH_LEAD")]
    stories = [s for s in get_stories() if s.get("status") not in ("CLOSED",) and s.get("priority") != "CRITICAL"]

    if not users or len(stories) < 6:
        print("[Chaos] Not enough data. Skipping.")
        return

    victim = random.choice(users)
    to_assign = random.sample(stories, min(6, len(stories)))

    try:
        for s in to_assign:
            requests.patch(f"{SIM_API}/stories/{s['id']}", json={
                "assignee_id": victim["id"], "priority": "CRITICAL"
            }, timeout=5)

        print(f"[Chaos] SUCCESS: {victim.get('email', 'unknown')} overloaded with {len(to_assign)} CRITICAL tasks.")
    except Exception as e:
        print(f"[Chaos Error] {e}")

def inject_priority_escalation():
    """Fault Pattern 3: Escalates a LOW priority ticket to CRITICAL."""
    print("\n[Chaos] Attempting to inject PRIORITY_ESCALATION...")
    stories = [s for s in get_stories() if s.get("priority") == "LOW" and s.get("status") != "CLOSED"]
    if not stories:
        print("[Chaos] No LOW priority stories. Skipping.")
        return

    target = random.choice(stories)
    try:
        requests.patch(f"{SIM_API}/stories/{target['id']}", json={"priority": "CRITICAL"}, timeout=5)

        comment_text = generate_chaos_comment("This low priority bug just caused a Sev-1 production outage.")
        comment_payload = {
            "id": f"CMT-CHAOS-{os.urandom(4).hex()}",
            "story_id": target["id"],
            "author_id": target.get("reporter_id", "SYSTEM"),
            "body": f"ESCALATION: {comment_text}"
        }
        requests.post(f"{SIM_API}/comments", json=comment_payload, timeout=5)

        print(f"[Chaos] SUCCESS: {target.get('key')} escalated from LOW to CRITICAL.")
    except Exception as e:
        print(f"[Chaos Error] {e}")

def start_engine():
    """Starts the APScheduler to randomly fire chaos events."""
    scheduler = BackgroundScheduler()

    scheduler.add_job(inject_ticket_blocker, "interval", minutes=3, jitter=60)
    scheduler.add_job(inject_developer_overload, "interval", minutes=8, jitter=120)
    scheduler.add_job(inject_priority_escalation, "interval", minutes=5, jitter=60)

    scheduler.start()
    print("Chaos Engine Started. Injecting enterprise failures...")

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    start_engine()
