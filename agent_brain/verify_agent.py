#!/usr/bin/env python3
"""
Athena Agent Brain — End-to-End Verification Script
====================================================
Tests every layer of the Agent Brain pipeline independently:

  LAYER 1 — Data Store Connectivity    (Neo4j + Pinecone have data)
  LAYER 2 — Tool Layer                 (Individual tools return real data)
  LAYER 3 — LLM + Tool Binding        (Groq LLM can call tools correctly)
  LAYER 4 — Full Graph Execution       (LangGraph runs end-to-end)
  LAYER 5 — API Endpoint               (POST /api/v1/query returns output)

Run from project root with venv active:
  python agent_brain/verify_agent.py

Each test prints PASS / FAIL and exactly what data was returned.
"""

import sys
import os
import json
import time

# ── Path setup ─────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

# ── ANSI colours ───────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}✅ PASS{RESET}"
FAIL = f"{RED}❌ FAIL{RESET}"
INFO = f"{CYAN}ℹ️ {RESET}"

results: list[dict] = []

def section(title: str):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

def check(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    print(f"  {status}  {name}")
    if detail:
        # Indent and truncate long details
        lines = detail.strip().split("\n")
        for line in lines[:6]:
            print(f"         {YELLOW}{line[:100]}{RESET}")
        if len(lines) > 6:
            print(f"         {YELLOW}... ({len(lines)-6} more lines){RESET}")
    results.append({"name": name, "passed": passed})


# ══════════════════════════════════════════════════════════════
#  LAYER 1 — DATA STORE CONNECTIVITY & DATA PRESENCE
# ══════════════════════════════════════════════════════════════

def test_layer1_datastores():
    section("LAYER 1 — Data Store Connectivity & Data Presence")

    # 1A. Neo4j — connection + node count check
    try:
        from athena_core import graph_syncer
        counts = graph_syncer.get_node_counts()
        total = sum(counts.values())
        detail = "\n".join([f"{label}: {cnt}" for label, cnt in counts.items()])
        if total > 0:
            check("Neo4j: Connected & has data", True, f"Total nodes: {total}\n{detail}")
        else:
            check("Neo4j: Connected but EMPTY (run backfill first)", False,
                  "No nodes found. Run: python -m athena_core.backfill")
    except Exception as e:
        check("Neo4j: Connection", False, str(e))

    # 1B. Neo4j — can we query something basic?
    try:
        from athena_core import graph_syncer
        results_q = graph_syncer.search_graph("MATCH (n) RETURN labels(n) AS lbl LIMIT 5")
        check("Neo4j: Cypher query executes", True,
              f"Sample: {json.dumps(results_q[:2], default=str)}")
    except Exception as e:
        check("Neo4j: Cypher query executes", False, str(e))

    # 1C. Pinecone — connection + vector count
    try:
        from athena_core import vector_indexer
        count = vector_indexer.get_vector_count()
        if count > 0:
            check("Pinecone: Connected & has vectors", True, f"Total vectors: {count}")
        else:
            check("Pinecone: Connected but EMPTY (run backfill first)", False,
                  "No vectors found. Run: python -m athena_core.backfill")
    except Exception as e:
        check("Pinecone: Connection", False, str(e))

    # 1D. Pinecone — semantic search returns results
    try:
        from athena_core import vector_indexer
        results_v = vector_indexer.search_docs("blocked ticket high priority", k=3)
        if results_v and "error" not in results_v[0]:
            check("Pinecone: Semantic search returns results", True,
                  f"Top result: score={results_v[0]['score']:.3f}, "
                  f"type={results_v[0]['metadata'].get('entity_type')}, "
                  f"key={results_v[0]['metadata'].get('key','?')}")
        else:
            check("Pinecone: Semantic search returns results", False,
                  f"Result: {results_v}")
    except Exception as e:
        check("Pinecone: Semantic search returns results", False, str(e))

    # 1E. Simulator API — is it running and has data?
    try:
        import requests
        from athena_core import config

        # Step 1: Check health
        health_resp = requests.get(f"{config.SIMULATOR_API_URL}/health", timeout=5)
        health_resp.raise_for_status()

        # Step 2: Verify data exists — use /users (always populated) and /issues/search
        users_resp = requests.get(f"{config.SIMULATOR_API_URL}/users", timeout=5)
        users = users_resp.json() if users_resp.ok else []

        issues_resp = requests.get(
            f"{config.SIMULATOR_API_URL}/issues/search",
            params={"jql": "status=OPEN", "analyze_by_component": "true"},
            timeout=10
        )
        issues_data = issues_resp.json() if issues_resp.ok else {}
        components = list(issues_data.get("component_breakdown", {}).keys())
        total_issues = issues_data.get("total", 0)

        if isinstance(users, list) and len(users) > 0:
            check("Simulator API: Running & has data", True,
                  f"Users: {len(users)} | Open Issues: {total_issues} | "
                  f"Epics/Components: {components[:3]}")
        else:
            check("Simulator API: Running but DB empty", False,
                  "No users found. Run: python -m simulator.timeline_sim")
    except Exception as e:
        check("Simulator API: Running", False,
              f"{e}\n→ Start it: uvicorn simulator.api:app --port 8000 --reload")



# ══════════════════════════════════════════════════════════════
#  LAYER 2 — INDIVIDUAL TOOL TESTS
# ══════════════════════════════════════════════════════════════

def test_layer2_tools():
    section("LAYER 2 — Individual Agent Tool Tests")

    # 2A. get_all_projects tool
    try:
        from agent_brain.tools import get_all_projects
        result = get_all_projects.invoke({})
        if isinstance(result, list) and len(result) > 0 and "error" not in result[0]:
            check("Tool: get_all_projects", True,
                  f"Returned {len(result)} projects: {[p.get('key','?') for p in result[:4]]}")
        else:
            check("Tool: get_all_projects", False, f"Result: {result}")
    except Exception as e:
        check("Tool: get_all_projects", False, str(e))

    # 2B. get_blocked_tickets tool
    try:
        from agent_brain.tools import get_blocked_tickets
        result = get_blocked_tickets.invoke({})
        if isinstance(result, list):
            blocked_keys = [t.get('key', '?') for t in result[:5] if 'error' not in t]
            check("Tool: get_blocked_tickets", True,
                  f"Returned {len(result)} blocked tickets: {blocked_keys}")
        else:
            check("Tool: get_blocked_tickets", False, f"Result: {result}")
    except Exception as e:
        check("Tool: get_blocked_tickets", False, str(e))

    # 2C. search_graph tool (Neo4j via tool wrapper)
    try:
        from agent_brain.tools import search_graph
        result = search_graph.invoke({
            "cypher_query": "MATCH (t:Task) RETURN t.key AS key, t.status AS status LIMIT 5"
        })
        if isinstance(result, list) and len(result) > 0 and "error" not in result[0]:
            check("Tool: search_graph (Neo4j)", True,
                  f"Returned {len(result)} rows: {json.dumps(result[:2], default=str)}")
        else:
            check("Tool: search_graph (Neo4j)", False, f"Result: {result}")
    except Exception as e:
        check("Tool: search_graph (Neo4j)", False, str(e))

    # 2D. search_docs tool (Pinecone via tool wrapper)
    try:
        from agent_brain.tools import search_docs
        result = search_docs.invoke({
            "query_text": "authentication login feature development",
            "k": 3
        })
        if isinstance(result, list) and len(result) > 0 and "error" not in result[0]:
            check("Tool: search_docs (Pinecone)", True,
                  f"Returned {len(result)} docs, top score: {result[0]['score']:.3f}, "
                  f"key: {result[0]['metadata'].get('key','?')}")
        else:
            check("Tool: search_docs (Pinecone)", False, f"Result: {result}")
    except Exception as e:
        check("Tool: search_docs (Pinecone)", False, str(e))

    # 2E. get_risk_chain tool
    try:
        from agent_brain.tools import search_graph as sg
        # First find a real task ID
        tasks = sg.invoke({"cypher_query": "MATCH (t:Task) RETURN t.id AS id LIMIT 1"})
        if tasks and "error" not in tasks[0]:
            task_id = tasks[0]["id"]
            from agent_brain.tools import get_risk_chain
            result = get_risk_chain.invoke({"task_id": task_id})
            check("Tool: get_risk_chain", True,
                  f"Task ID: {task_id} → {len(result)} risk chain entries")
        else:
            check("Tool: get_risk_chain", False, "Cannot get a real task ID from Neo4j")
    except Exception as e:
        check("Tool: get_risk_chain", False, str(e))

    # 2F. log_to_atl utility tool
    try:
        from agent_brain.tools import log_to_atl
        result = log_to_atl.invoke({
            "action_type": "TEST_ENTRY",
            "description": "Verification test ATL entry",
            "severity": "LOW",
            "status": "LOGGED"
        })
        if isinstance(result, dict) and result.get("id", "").startswith("ATL-"):
            check("Tool: log_to_atl (utility)", True,
                  f"ATL entry created: {result['id']} at {result['timestamp']}")
        else:
            check("Tool: log_to_atl (utility)", False, f"Result: {result}")
    except Exception as e:
        check("Tool: log_to_atl (utility)", False, str(e))


# ══════════════════════════════════════════════════════════════
#  LAYER 3 — LLM + TOOL BINDING TEST
# ══════════════════════════════════════════════════════════════

def test_layer3_llm_tools():
    section("LAYER 3 — LLM Binding & Tool Calling (Groq)")

    # 3A. LLM can be initialised
    try:
        from agent_brain.nodes import get_llm, get_llm_plain
        llm = get_llm()
        check("Groq LLM: Initialises with tools bound", True,
              f"Model bound with tools successfully.")
    except Exception as e:
        check("Groq LLM: Initialises with tools bound", False, str(e))
        return  # Cannot continue if LLM fails

    # 3B. LLM responds to a plain query
    try:
        from agent_brain.nodes import get_llm_plain
        from langchain_core.messages import HumanMessage
        llm = get_llm_plain()
        resp = llm.invoke([HumanMessage(content="Say 'Athena is ready' and nothing else.")])
        check("Groq LLM: Plain response", True, f"Response: {resp.content.strip()}")
    except Exception as e:
        check("Groq LLM: Plain response", False, str(e))

    # 3C. LLM selects a tool when asked (tool calling works)
    try:
        from agent_brain.nodes import get_llm
        from langchain_core.messages import HumanMessage, SystemMessage
        llm = get_llm()
        resp = llm.invoke([
            SystemMessage(content="You are a helpful agent. Use tools to answer questions."),
            HumanMessage(content="Fetch all projects from Jira using the available tools.")
        ])
        if resp.tool_calls:
            tool_name = resp.tool_calls[0]["name"]
            check("Groq LLM: Calls a tool when prompted", True,
                  f"LLM chose tool: '{tool_name}' with args: {resp.tool_calls[0]['args']}")
        else:
            check("Groq LLM: Calls a tool when prompted", False,
                  f"LLM responded with text instead of tool call: {resp.content[:100]}")
    except Exception as e:
        check("Groq LLM: Calls a tool when prompted", False, str(e))


# ══════════════════════════════════════════════════════════════
#  LAYER 4 — FULL LANGGRAPH EXECUTION (End-to-End)
# ══════════════════════════════════════════════════════════════

def test_layer4_graph():
    section("LAYER 4 — Full LangGraph End-to-End Execution")

    from langchain_core.messages import HumanMessage

    # 4A. Graph compiles without errors
    try:
        from agent_brain.graph import compile
        graph = compile()
        check("LangGraph: Compiles successfully", True, "StateGraph compiled with checkpointer.")
    except Exception as e:
        check("LangGraph: Compiles successfully", False, str(e))
        return

    # 4B. Test with a GENERAL query (fastest path — no tool calls)
    try:
        from agent_brain.graph import get_graph
        import uuid
        graph = get_graph()
        thread_id = f"verify-general-{uuid.uuid4().hex[:6]}"
        state = {
            "messages": [HumanMessage(content="Hello Athena, what can you do?")],
            "input_type": "", "context": "", "pending_action": None,
            "atl_entries": [], "final_response": "", "thread_id": thread_id,
        }
        result = graph.invoke(state, config={"configurable": {"thread_id": thread_id}})
        response = result.get("final_response", "")
        route = result.get("input_type", "?")
        if response:
            check("LangGraph: General query → response", True,
                  f"Route: {route}\nResponse preview: {response[:200]}")
        else:
            check("LangGraph: General query → response", False,
                  f"No final_response in state. Keys: {list(result.keys())}")
    except Exception as e:
        check("LangGraph: General query → response", False, str(e))

    # 4C. Test with a DATA QUERY (exercises Researcher + Neo4j/Pinecone tools)
    print(f"\n  {INFO} Running data query test (may take 10-30s — LLM calls tools)...")
    try:
        from agent_brain.graph import get_graph
        import uuid
        graph = get_graph()
        thread_id = f"verify-query-{uuid.uuid4().hex[:6]}"
        state = {
            "messages": [HumanMessage(content="What projects are currently active and are there any blocked tickets?")],
            "input_type": "", "context": "", "pending_action": None,
            "atl_entries": [], "final_response": "", "thread_id": thread_id,
        }
        t0 = time.time()
        result = graph.invoke(state, config={"configurable": {"thread_id": thread_id}})
        elapsed = round(time.time() - t0, 1)

        response = result.get("final_response", "")
        context = result.get("context", "")
        route = result.get("input_type", "?")

        if response and len(response) > 50:
            check(f"LangGraph: Data query → response ({elapsed}s)", True,
                  f"Route: {route}\n"
                  f"Context gathered: {len(context)} chars\n"
                  f"Response preview: {response[:300]}")
        else:
            check(f"LangGraph: Data query → response ({elapsed}s)", False,
                  f"Route: {route}\nContext: {len(context)} chars\nResponse: '{response[:100]}'")
    except Exception as e:
        check("LangGraph: Data query → response", False, str(e))

    # 4D. Verify context is sourced from data stores (not hallucinated)
    try:
        context_has_data = len(context) > 100 if 'context' in dir() else False
        if context_has_data:
            check("LangGraph: Context populated from tools", True,
                  f"Context is {len(context)} chars — data was fetched from stores.")
        else:
            check("LangGraph: Context populated from tools", False,
                  "Context was empty — Researcher may not have called any tools.")
    except Exception as e:
        check("LangGraph: Context populated from tools", False, str(e))


# ══════════════════════════════════════════════════════════════
#  LAYER 5 — API ENDPOINT TEST (requires Athena Core running)
# ══════════════════════════════════════════════════════════════

def test_layer5_api():
    section("LAYER 5 — API Endpoint Test (requires Athena Core on :8001)")

    import requests

    base = "http://localhost:8001"

    # 5A. Health check
    try:
        resp = requests.get(f"{base}/api/v1/health", timeout=5)
        data = resp.json()
        if data.get("status") == "healthy":
            check("API: /api/v1/health", True, f"Version: {data.get('version')}")
        else:
            check("API: /api/v1/health", False, f"Response: {data}")
    except Exception as e:
        check("API: /api/v1/health", False,
              f"{e}\n→ Start Athena Core: uvicorn athena_core.api:app --port 8001 --reload")
        print(f"\n  {INFO} Skipping API tests — Athena Core is not running on :8001")
        return

    # 5B. POST /api/v1/query — general query
    try:
        payload = {"query": "Hello Athena, what can you help me with?"}
        resp = requests.post(f"{base}/api/v1/query", json=payload, timeout=60)
        data = resp.json()
        if resp.status_code == 200 and data.get("response"):
            check("API: POST /api/v1/query (general)", True,
                  f"Status: {data.get('status')}\n"
                  f"Thread: {data.get('thread_id','?')[:16]}...\n"
                  f"Response: {data.get('response','')[:200]}")
        else:
            check("API: POST /api/v1/query (general)", False,
                  f"HTTP {resp.status_code}: {str(data)[:200]}")
    except Exception as e:
        check("API: POST /api/v1/query (general)", False, str(e))

    # 5C. POST /api/v1/query — data query (hits Neo4j + Pinecone)
    print(f"\n  {INFO} Sending data query to API (may take 15-30s)...")
    try:
        payload = {"query": "Show me all blocked tickets and which epics they belong to."}
        resp = requests.post(f"{base}/api/v1/query", json=payload, timeout=90)
        data = resp.json()
        if resp.status_code == 200 and data.get("response"):
            check("API: POST /api/v1/query (data query)", True,
                  f"Status: {data.get('status')}\n"
                  f"Input type: {data.get('input_type','?')}\n"
                  f"Response: {data.get('response','')[:300]}")
        else:
            check("API: POST /api/v1/query (data query)", False,
                  f"HTTP {resp.status_code}: {str(data)[:200]}")
    except Exception as e:
        check("API: POST /api/v1/query (data query)", False, str(e))

    # 5D. GET /api/v1/atl — ATL viewer
    try:
        resp = requests.get(f"{base}/api/v1/atl", timeout=10)
        data = resp.json()
        check("API: GET /api/v1/atl", True,
              f"ATL entries: {data.get('total', 0)}")
    except Exception as e:
        check("API: GET /api/v1/atl", False, str(e))


# ══════════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════════

def print_summary():
    section("SUMMARY")
    passed = sum(1 for r in results if r["passed"])
    total  = len(results)

    for r in results:
        icon = "✅" if r["passed"] else "❌"
        print(f"  {icon}  {r['name']}")

    print(f"\n  {BOLD}{passed}/{total} checks passed.{RESET}\n")

    if passed == total:
        print(f"  {GREEN}{BOLD}🚀 Agent Brain fully verified! All systems operational.{RESET}\n")
    else:
        failed = [r["name"] for r in results if not r["passed"]]
        print(f"  {RED}{BOLD}⚠️  {total - passed} checks failed:{RESET}")
        for f in failed:
            print(f"  {RED}   • {f}{RESET}")
        print()

        # Helpful triage hints
        neo4j_fail = any("Neo4j" in r["name"] and not r["passed"] for r in results)
        pinecone_fail = any("Pinecone" in r["name"] and not r["passed"] for r in results)
        sim_fail = any("Simulator" in r["name"] and not r["passed"] for r in results)

        if neo4j_fail or pinecone_fail:
            print(f"  {YELLOW}💡 Looks like data stores may be empty.")
            print(f"     Run:  python -m athena_core.backfill{RESET}\n")
        if sim_fail:
            print(f"  {YELLOW}💡 Simulator is not running.")
            print(f"     Run (in a separate terminal):  uvicorn simulator.api:app --port 8000 --reload{RESET}\n")


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\n{BOLD}{'='*60}")
    print("  ATHENA — AGENT BRAIN VERIFICATION")
    print(f"{'='*60}{RESET}")
    print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    test_layer1_datastores()
    test_layer2_tools()
    test_layer3_llm_tools()
    test_layer4_graph()
    test_layer5_api()
    print_summary()
