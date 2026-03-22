"""
SomaAgent v2 — Reasoning Node
Uses Ollama LLM to interpret Laban movement data and generate artistic interpretations,
NFT metadata, and autonomous minting decisions.
"""
import sys
import pathlib
import json
import threading

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from agent.state import AgentState
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_API_KEY


class TimeoutException(Exception):
    pass


def _call_ollama(prompt: str, timeout_sec=5) -> str:
    """Call Ollama LLM with timeout. Returns response text or empty string if timeout."""
    try:
        from langchain_ollama import OllamaLLM
        
        # Initialize Ollama LLM
        llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7
        )
        
        result = []
        exception = [None]
        
        def call_with_timeout():
            try:
                response = llm.invoke(prompt)
                result.append(str(response))
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=call_with_timeout, daemon=True)
        thread.start()
        thread.join(timeout=timeout_sec)
        
        if thread.is_alive():
            print(f"[REASONING]   ⏱️ Ollama timeout ({timeout_sec}s) - skipping")
            return ""
        
        if exception[0]:
            print(f"[REASONING]   ❌ Ollama error - skipping")
            return ""
        
        return result[0] if result else ""
        
    except ImportError:
        print("[REASONING]   ℹ️ langchain-ollama not installed - using fallback")
        return ""
    except Exception as e:
        print(f"[REASONING]   ❌ Ollama init error - using fallback")
        return ""


def reasoning_node(state: AgentState) -> AgentState:
    """
    LangGraph node: Process REAL Laban data with Ollama LLM.
    Generates artistic interpretation, NFT metadata, and minting decision.
    """
    print(f"\n[REASONING] ✓ Initializing reasoning...")

    laban_scores = state.get("laban_scores")
    dominant = state.get("dominant_movement")
    confidence = state.get("movement_confidence")

    # FAIL if no real data
    if not laban_scores or not dominant:
        error = "❌ NO REAL LABAN DATA RECEIVED"
        print(f"[REASONING] {error}")
        return {
            **state,
            "error": error,
            "status": "error",
            "next_action": "end"
        }

    # Print real data captured
    print(f"[REASONING] 📊 LABAN MOVEMENT ANALYSIS")
    print(f"  Session: {state.get('session_id', 'unknown')[:8]}")
    print(f"  Dominant: {dominant} ({confidence:.0%} confidence)")
    print(f"  Scores:")
    for movement, score in sorted(laban_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"    • {movement}: {score:.1%}")

    # ─── GENERATE METADATA (with or without LLM) ──────────────────────────────
    
    # Hardcoded movement descriptions (fallback)
    movement_descriptions = {
        'tocar': ('The Gentle Touch', 'A delicate exploration through space, fingers tracing invisible paths'),
        'golpear': ('Strike Force', 'Powerful percussive movements, energy released through sharp gestures'),
        'flotar': ('Weightless Drift', 'Suspended elegance, movements flowing as if defying gravity'),
        'deslizar': ('Sliding Motion', 'Smooth, gliding transitions across planes of existence'),
        'cortar': ('Clean Cut', 'Precise movements slicing through space with decisive intent'),
        'presionar': ('Pressure Point', 'Grounded force meeting resistance, controlled strength'),
        'retorcer': ('Twisted Form', 'Spiraling, winding movements that fold space around the body'),
        'sacudir': ('Trembling Energy', 'Rapid vibrations releasing tension and kinetic power'),
    }
    
    # Get fallback title and description
    default_title, default_desc = movement_descriptions.get(dominant, (f'{dominant.capitalize()} Movement', 'An exploration of space and energy through deliberate motion'))
    
    # Try Ollama for better titles (with SHORT timeout)
    print(f"[REASONING] 💡 Requesting LLM interpretation...")
    
    interpretation_prompt = f"""In 1-2 poetic sentences, interpret this Laban movement: {dominant} ({confidence:.0%} confidence).
Focus on emotion and visual metaphor. Be brief."""
    
    artistic_interpretation = _call_ollama(interpretation_prompt, timeout_sec=3)
    
    if not artistic_interpretation or artistic_interpretation == "":
        print(f"[REASONING] ↪️ LLM unavailable, using pre-trained description")
        artistic_interpretation = default_desc
        nft_title = default_title
        keywords = [dominant, 'kinetic', 'embodied', 'laban']
        emotion = 'dynamic'
    else:
        print(f"[REASONING] ✅ LLM response ({len(artistic_interpretation)} chars)")
        nft_title = f"Movement: {dominant.capitalize()}"
        keywords = [dominant, 'kinetic', 'embodied']
        emotion = 'dynamic'

    print(f"[REASONING] 🎨 Title: {nft_title}")
    print(f"[REASONING] 🏷️ Keywords: {', '.join(keywords)}")
    print(f"[REASONING] 💫 Emotion: {emotion}")

    # ─── MINTING DECISION ───────────────────────────────────────────────────────
    print(f"\n[REASONING] 🚀 MINTING DECISION: ✅ AUTO-MINT")
    should_mint = True

    return {
        **state,
        "session_id": state.get("session_id") or str(__import__('uuid').uuid4())[:8],
        "reasoning_chain": "Laban-based movement analysis + LLM interpretation",
        "artistic_interpretation": artistic_interpretation,
        "nft_title": nft_title,
        "nft_description": artistic_interpretation,
        "visual_keywords": keywords,
        "emotion_tag": emotion,
        "should_mint": should_mint,
        "status": "success",
        "next_action": "log"
    }
