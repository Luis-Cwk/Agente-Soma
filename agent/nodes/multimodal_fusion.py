"""
SomaAgent — Multimodal Fusion Node
─────────────────────────────────────────────────────────────────────────────
Enriches Laban movement data with visual context from video_analyzer.
Combines perception (Laban) + vision (LLaVA + MediaPipe) to calculate rarity.

READS FROM:
  - perception node output: laban_scores, dominant_movement, movement_confidence
  - video_analyzer output (via callback): body_openness, emotional_intensity, etc.

WRITES TO:
  - State fields: combined_rarity_score, rarity_tier, suggested_price_eth, 
                  enriched_context, visual_context (new fields)

PRESERVES:
  - All existing perception and reasoning data (non-breaking)
  - Original Laban scores and movement classification (unchanged)
  - Existing graph routing (perception → multimodal_fusion → reasoning)
"""
from typing import Dict, Any, Optional, Callable
from langchain_core.runnables import RunnableConfig

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from agent.state import AgentState


# ─── Visual Context Data Structure ────────────────────────────────────────────

def create_empty_visual_context() -> Dict[str, Any]:
    """Create default visual context when video_analyzer not available."""
    return {
        "body_openness": 0.5,           # Default neutral
        "emotional_intensity": "neutral",
        "arm_velocity": 0.5,
        "energy_level": "neutral",
        "spatial_coverage": 0.5,
        "llava_description": "Analysis unavailable",
        "video_keypoints": [],
        "body_angles": {},
        "source": "default"     # Marker: real data vs fallback
    }


# ─── Rarity Calculation ───────────────────────────────────────────────────────

def _calculate_combined_rarity(laban_confidence: float, visual_context: Dict) -> Dict[str, Any]:
    """
    Fuse Laban confidence + visual context to calculate combined rarity.
    
    Formula:
        combined = (laban_confidence * 0.60) + (openness * intensity_factor * 0.40)
    
    Args:
        laban_confidence: Movement confidence from Laban analysis (0.0-1.0)
        visual_context: Dict with body_openness, emotional_intensity, etc.
    
    Returns:
        Dict with combined_rarity_score, rarity_tier, suggested_price_eth
    """
    
    # Base rarity from Laban classification
    laban_rarity = laban_confidence
    
    # Visual context boost
    openness = visual_context.get("body_openness", 0.5)
    intensity = visual_context.get("emotional_intensity", "neutral")
    
    # Convert intensity to numeric factor
    intensity_factor = {
        "low": 0.4,
        "calm": 0.4,
        "neutral": 0.6,
        "medium": 0.7,
        "high": 1.0,
        "intense": 1.0,
    }.get(intensity.lower(), 0.6)
    
    # Weighted fusion
    visual_rarity = openness * intensity_factor
    combined_rarity = (laban_rarity * 0.60) + (visual_rarity * 0.40)
    combined_rarity = min(1.0, combined_rarity)  # Cap at 1.0
    
    # Determine rarity tier
    if combined_rarity > 0.85:
        tier = "EPIC"
        price = 0.25
    elif combined_rarity > 0.70:
        tier = "RARE"
        price = 0.10
    elif combined_rarity > 0.55:
        tier = "UNCOMMON"
        price = 0.05
    else:
        tier = "COMMON"
        price = 0.01
    
    return {
        "combined_rarity_score": round(combined_rarity, 3),
        "rarity_tier": tier,
        "suggested_price_eth": price,
        "openness_factor": round(openness, 3),
        "intensity_factor": round(intensity_factor, 3),
    }


def _create_enriched_context(
    laban_data: Dict[str, Any],
    visual_data: Dict[str, Any],
    rarity_data: Dict[str, Any]
) -> str:
    """
    Create enriched text context for LLM reasoning.
    Combines Laban + visual signals into a narrative prompt.
    
    Args:
        laban_data: Output from perception node
        visual_data: Output from video_analyzer (or defaults)
        rarity_data: Calculated rarity scores
    
    Returns:
        Rich context string for LLM
    """
    
    context = f"""
    ─── MULTIMODAL MOVEMENT DATA ───
    
    Primary Movement: {laban_data['dominant_movement']}
    Movement Confidence: {laban_data['movement_confidence']:.1%}
    
    Laban Scores (All 8 Efforts):
    {format_laban_scores(laban_data['laban_scores'])}
    
    ─── VISUAL CONTEXT (from video analysis) ───
    Body Openness: {visual_data.get('body_openness', 0.5):.1%}
    Emotional Intensity: {visual_data.get('emotional_intensity', 'unknown')}
    Arm Velocity: {visual_data.get('arm_velocity', 0.5):.1%}
    Energy Level: {visual_data.get('energy_level', 'unknown')}
    Spatial Coverage: {visual_data.get('spatial_coverage', 0.5):.1%}
    
    ─── FUSION ANALYSIS ───
    Combined Rarity Score: {rarity_data['combined_rarity_score']:.1%}
    Rarity Tier: {rarity_data['rarity_tier']}
    Suggested Minting Price: {rarity_data['suggested_price_eth']} ETH
    
    ─── VISUAL INTERPRETATION ───
    {visual_data.get('llava_description', 'No visual description available').strip()}
    
    ─── INSTRUCTIONS FOR LLM ───
    Use this multimodal data to generate:
    1. Artistic description (70% movement + 30% emotional context)
    2. NFT metadata with rarity signals
    3. Minting recommendation (confidence threshold: {rarity_data['combined_rarity_score']:.1%})
    """
    
    return context


def format_laban_scores(scores: Dict[str, float]) -> str:
    """Format Laban scores as readable table."""
    lines = []
    for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        bar_length = int(score * 20)  # Visual bar
        bar = "█" * bar_length + "░" * (20 - bar_length)
        lines.append(f"    {name:10s} │{bar}│ {score:.1%}")
    return "\n".join(lines) if lines else "    (no scores)"


# ─── Main Fusion Node ─────────────────────────────────────────────────────────

def multimodal_fusion_node(
    state: AgentState,
    *,
    visual_context_provider: Optional[Callable] = None,
    config: RunnableConfig | None = None
) -> AgentState:
    """
    LangGraph node: Fuse Laban data with visual context for enriched reasoning.
    
    This node sits between perception and reasoning:
    - Reads: laban_scores, dominant_movement, movement_confidence (from perception)
    - Computes: combined_rarity_score, rarity_tier, suggested_price_eth
    - Reads: visual context (body_openness, emotional_intensity, etc.)
    - Outputs: enriched_context for LLM
    
    Non-breaking: All input data is preserved unchanged.
    
    Args:
        state: AgentState from perception node
        visual_context_provider: Optional callback to fetch video_analyzer data
        config: LangGraph config (ignored for now)
    
    Returns:
        Updated AgentState with multimodal fusion results
    """
    
    # Validate perception data
    if not state.get("laban_scores") or not state.get("dominant_movement"):
        error_msg = "❌ MULTIMODAL FUSION: No Laban data from perception. Skipping fusion."
        print(f"[FUSION] {error_msg}")
        return {
            **state,
            "error": error_msg,
            "status": "error",
            "next_action": "end"
        }
    
    laban_scores = state["laban_scores"]
    dominant_movement = state["dominant_movement"]
    movement_confidence = state.get("movement_confidence", 0.5)
    
    print(f"[FUSION] Starting multimodal fusion...")
    print(f"[FUSION] Input: {dominant_movement} ({movement_confidence:.1%} confidence)")
    
    # ─── Get visual context ─────────────────────────────────────────────────
    # Priority 1: Use provided callback (from video_analyzer integration)
    # Priority 2: Use static fallback
    
    if visual_context_provider and callable(visual_context_provider):
        try:
            print(f"[FUSION] Retrieving visual context from provider...")
            visual_context = visual_context_provider(state)
            source = "live_video_analyzer"
        except Exception as e:
            print(f"[FUSION] ⚠️ Visual context provider failed: {e}")
            visual_context = create_empty_visual_context()
            visual_context["source"] = "fallback_after_error"
            source = "fallback"
    else:
        print(f"[FUSION] No visual provider configured, using default context")
        visual_context = create_empty_visual_context()
        source = "default"
    
    print(f"[FUSION] Visual context source: {visual_context.get('source', source)}")
    
    # ─── Calculate rarity ─────────────────────────────────────────────────
    rarity_data = _calculate_combined_rarity(movement_confidence, visual_context)
    
    print(f"[FUSION] ✓ Rarity calculated: {rarity_data['rarity_tier']} "
          f"({rarity_data['combined_rarity_score']:.1%})")
    
    # ─── Create enriched context for LLM ──────────────────────────────────
    enriched_context = _create_enriched_context(
        {
            "dominant_movement": dominant_movement,
            "movement_confidence": movement_confidence,
            "laban_scores": laban_scores,
        },
        visual_context,
        rarity_data
    )
    
    # ─── Return updated state ─────────────────────────────────────────────
    
    updated_state = {
        **state,
        
        # Preserve all existing data (non-breaking)
        "laban_scores": laban_scores,
        "dominant_movement": dominant_movement,
        "movement_confidence": movement_confidence,
        
        # Add new multimodal fields
        "visual_context": visual_context,
        "combined_rarity_score": rarity_data["combined_rarity_score"],
        "rarity_tier": rarity_data["rarity_tier"],
        "suggested_price_eth": rarity_data["suggested_price_eth"],
        "enriched_context": enriched_context,
        
        # Status for routing
        "status": "running",
        "next_action": "reasoning"
    }
    
    print(f"[FUSION] ✓ Multimodal fusion complete")
    print(f"[FUSION] Ready for reasoning with enriched context\n")
    
    return updated_state
