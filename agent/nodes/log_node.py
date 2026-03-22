"""
SomaAgent — ERC-8004 Log Node
Generates a verifiable agent_log.json with hash chain.
Every decision the agent made is recorded and cryptographically chained.
This is the core of the ERC-8004 "Agents With Receipts" bounty.
"""
import json
import hashlib
import time
import sys
import pathlib
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from config import LOG_DIR, AGENT_NAME, AGENT_VERSION, AGENT_TEAM_ID, AGENT_REG_TX
from agent.state import AgentState


def _sha256(data: dict) -> str:
    """Compute SHA-256 hash of a JSON-serializable dict."""
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _load_prev_hash(session_id: str) -> str:
    """Load previous session hash for chaining. Returns genesis hash if first."""
    chain_file = LOG_DIR / "hash_chain.json"
    if chain_file.exists():
        try:
            chain = json.loads(chain_file.read_text())
            return chain.get("last_hash", "0" * 64)
        except Exception:
            pass
    return "0" * 64  # Genesis block


def _save_hash_chain(session_id: str, log_hash: str):
    """Persist the latest hash for the next session's chain."""
    chain_file = LOG_DIR / "hash_chain.json"
    chain = {
        "last_session_id": session_id,
        "last_hash": log_hash,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    chain_file.write_text(json.dumps(chain, indent=2))


def log_node(state: AgentState) -> AgentState:
    """
    LangGraph node: Build ERC-8004 compliant agent_log with hash chain.
    """
    print(f"[LOG] Building ERC-8004 agent_log...")

    session_id = state.get("session_id", "unknown")
    prev_hash = _load_prev_hash(session_id)

    # ─── Build the structured decision log ────────────────────────────────────
    log_entries = [
        {
            "step": 1,
            "node": "perception",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "motion_capture",
            "input": {
                "duration_seconds": "configured",
                "camera_index": "configured"
            },
            "output": {
                "dominant_movement": state.get("dominant_movement"),
                "confidence": state.get("movement_confidence"),
                "laban_scores": state.get("laban_scores"),
                "frames_captured": len(state.get("raw_landmarks") or [])
            },
            "decision": f"Detected '{state.get('dominant_movement')}' as primary movement quality"
        },
        {
            "step": 2,
            "node": "reasoning",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "artistic_decision",
            "input": {
                "model": AGENT_VERSION,
                "laban_context": state.get("dominant_movement"),
                "reasoning_steps_count": len(state.get("reasoning_chain") or [])
            },
            "output": {
                "nft_title": state.get("nft_title"),
                "emotion_tag": state.get("emotion_tag"),
                "visual_keywords": state.get("visual_keywords"),
                "reasoning_chain": state.get("reasoning_chain")
            },
            "decision": f"Agent decided to frame movement as '{state.get('emotion_tag')}' artwork"
        }
    ]

    # ─── Compute entry hashes ─────────────────────────────────────────────────
    for entry in log_entries:
        entry["entry_hash"] = _sha256(entry)

    # ─── Build full log document ──────────────────────────────────────────────
    log_doc = {
        "schema": "ERC-8004-v1",
        "agent": {
            "name": AGENT_NAME,
            "version": AGENT_VERSION,
            "team_id": AGENT_TEAM_ID,
            "registration_tx": AGENT_REG_TX,
        },
        "session": {
            "id": session_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "pipeline": "perception → reasoning → log → publish"
        },
        "prev_log_hash": prev_hash,
        "entries": log_entries,
        "summary": {
            "dominant_movement": state.get("dominant_movement"),
            "nft_title": state.get("nft_title"),
            "nft_description": state.get("nft_description"),
            "artistic_interpretation": state.get("artistic_interpretation"),
            "emotion_tag": state.get("emotion_tag"),
            "visual_keywords": state.get("visual_keywords"),
        }
    }

    # ─── Final hash (chains to previous) ─────────────────────────────────────
    log_hash = _sha256({
        "prev_log_hash": prev_hash,
        "entries": [e["entry_hash"] for e in log_entries],
        "session_id": session_id
    })
    log_doc["log_hash"] = log_hash

    # ─── Persist to disk ──────────────────────────────────────────────────────
    log_path = LOG_DIR / f"agent_log_{session_id[:8]}.json"
    log_path.write_text(json.dumps(log_doc, indent=2, ensure_ascii=False), encoding='utf-8')
    _save_hash_chain(session_id, log_hash)
    
    print(f"[LOG] agent_log saved: {log_path.name}")
    print(f"[LOG] Hash: {log_hash[:16]}...{log_hash[-8:]}")
    print(f"[LOG] Chain: {prev_hash[:8]}... → {log_hash[:8]}...")

    return {
        **state,
        "log_entries": log_entries,
        "log_hash": log_hash,
        "prev_log_hash": prev_hash,
        "status": "running",
        "next_action": "publish"
    }
