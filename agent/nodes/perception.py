"""
SomaAgent v2 — Perception Node
Captures motion via MediaPipe and classifies into 8 Laban movement qualities.
"""
import cv2
import uuid
import time
import numpy as np
from typing import Dict, List, Optional, Any
from langchain_core.runnables import RunnableConfig

# MediaPipe imports
import mediapipe as mp
solutions = mp.solutions

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from config import CAMERA_INDEX, CAPTURE_SECONDS, MIN_CONFIDENCE
from agent.state import AgentState


# ─── Laban Movement Classifier ────────────────────────────────────────────────

LABAN_MOVEMENTS = {
    "golpear":  {"tiempo": "sudden",    "peso": "strong",  "espacio": "direct",   "flujo": "bound"},
    "flotar":   {"tiempo": "sustained", "peso": "light",   "espacio": "indirect", "flujo": "free"},
    "deslizar": {"tiempo": "sustained", "peso": "light",   "espacio": "direct",   "flujo": "free"},
    "cortar":   {"tiempo": "sudden",    "peso": "light",   "espacio": "indirect", "flujo": "bound"},
    "presionar": {"tiempo": "sustained","peso": "strong",  "espacio": "direct",   "flujo": "bound"},
    "retorcer": {"tiempo": "sustained", "peso": "strong",  "espacio": "indirect", "flujo": "bound"},
    "sacudir":  {"tiempo": "sudden",    "peso": "light",   "espacio": "indirect", "flujo": "free"},
    "tocar":    {"tiempo": "sudden",    "peso": "strong",  "espacio": "indirect", "flujo": "free"},
}


def _compute_laban_scores(frame_data: List[Dict]) -> Dict[str, float]:
    """
    Compute Laban scores from landmark sequences.
    Derives movement qualities from velocity, acceleration, trajectory variance.
    Returns normalized scores for each of the 8 Laban efforts.
    """
    if not frame_data or len(frame_data) < 5:
        return {k: 0.0 for k in LABAN_MOVEMENTS}

    # Extract wrist/shoulder velocities as proxy for effort
    velocities = []
    accelerations = []

    for i in range(1, len(frame_data)):
        prev = frame_data[i - 1].get("landmarks", [])
        curr = frame_data[i].get("landmarks", [])
        if not prev or not curr:
            continue

        # Wrist (16) and shoulder (12) landmarks
        for idx in [11, 12, 15, 16]:
            if idx < len(prev) and idx < len(curr):
                dx = curr[idx]["x"] - prev[idx]["x"]
                dy = curr[idx]["y"] - prev[idx]["y"]
                vel = np.sqrt(dx**2 + dy**2)
                velocities.append(vel)

    if not velocities:
        return {k: 0.0 for k in LABAN_MOVEMENTS}

    avg_vel = np.mean(velocities)
    vel_std = np.std(velocities)

    # Derive Laban dimensions from signal characteristics
    # Tiempo: sudden = high velocity variance; sustained = low variance
    tiempo_sudden = min(1.0, vel_std / 0.05)
    tiempo_sustained = 1.0 - tiempo_sudden

    # Peso: strong = high avg velocity; light = low avg velocity
    peso_strong = min(1.0, avg_vel / 0.03)
    peso_light = 1.0 - peso_strong

    # Espacio: direct = low trajectory spread; indirect = high spread
    if len(frame_data) > 2:
        xs = [f["landmarks"][15]["x"] for f in frame_data
              if f.get("landmarks") and len(f["landmarks"]) > 15]
        ys = [f["landmarks"][15]["y"] for f in frame_data
              if f.get("landmarks") and len(f["landmarks"]) > 15]
        spread = (np.std(xs) + np.std(ys)) if xs and ys else 0.01
    else:
        spread = 0.01

    espacio_indirect = min(1.0, spread / 0.1)
    espacio_direct = 1.0 - espacio_indirect

    # Flujo: free = smooth (low jerk); bound = jerky (high jerk)
    flujo_free = max(0.0, 1.0 - vel_std * 10)
    flujo_bound = 1.0 - flujo_free

    # Score each Laban movement against derived dimensions
    scores = {}
    for name, qualities in LABAN_MOVEMENTS.items():
        score = 0.0
        score += tiempo_sudden    if qualities["tiempo"]  == "sudden"    else tiempo_sustained
        score += peso_strong      if qualities["peso"]    == "strong"     else peso_light
        score += espacio_direct   if qualities["espacio"] == "direct"     else espacio_indirect
        score += flujo_bound      if qualities["flujo"]   == "bound"      else flujo_free
        scores[name] = round(score / 4.0, 3)

    # Normalize to sum to 1
    total = sum(scores.values()) or 1.0
    return {k: round(v / total, 3) for k, v in scores.items()}


def perception_node(state: AgentState, *, config: RunnableConfig | None = None) -> AgentState:
    """
    LangGraph node: Open camera, capture motion, compute Laban scores.
    Uses default camera from config.
    """
    if config is None:
        config = {}
    
    # Extract capture duration from config if available
    config_data = config.get("configurable", {}) if isinstance(config, dict) else {}
    capture_duration = config_data.get('capture_seconds', CAPTURE_SECONDS)
    
    # Always use the default camera
    camera_index = CAMERA_INDEX
    
    print(f"[PERCEPTION] Starting {capture_duration}s motion capture on camera {camera_index}...")

    pose = solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=MIN_CONFIDENCE,
        min_tracking_confidence=MIN_CONFIDENCE
    )

    frame_data = []
    start_time = time.time()
    session_id = str(uuid.uuid4())

    print(f"[PERCEPTION] Session {session_id} — Recording...")
    
    # Helper function to safely open camera with retry logic
    def open_camera(idx, retries=3):
        for attempt in range(retries):
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap.isOpened():
                    # Set reasonable defaults
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Test: try to read one frame
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        print(f"[PERCEPTION] ✓ Camera {idx} opened successfully")
                        return cap
                    cap.release()
            except Exception as e:
                print(f"[PERCEPTION] Camera {idx} attempt {attempt+1} failed: {e}")
            
            time.sleep(0.3)
        return None
    
    cap = open_camera(camera_index)
    if cap is None:
        error_msg = f"❌ Cannot open camera {camera_index}. Check connections."
        print(f"[PERCEPTION] {error_msg}")
        return {
            **state,
            "error": error_msg,
            "status": "error",
            "next_action": "end"
        }

    try:
        while (time.time() - start_time) < capture_duration:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                landmarks = [
                    {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                    for lm in results.pose_landmarks.landmark
                ]
                frame_data.append({
                    "timestamp": time.time() - start_time,
                    "landmarks": landmarks
                })

            # Visual feedback - skeleton only on black background
            try:
                # Create black canvas same size as frame
                h, w = frame.shape[:2]
                skeleton_frame = np.zeros((h, w, 3), dtype=np.uint8)
                
                # Draw landmarks on black background
                solutions.drawing_utils.draw_landmarks(
                    skeleton_frame, results.pose_landmarks, solutions.pose.POSE_CONNECTIONS
                )
                cv2.imshow("SomaAgent — Perception", skeleton_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception:
                pass  # Headless mode OK
    
    finally:
        cap.release()
        pose.close()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    if not frame_data:
        # NO FALLBACK - fail clearly if no real data
        error_msg = "❌ NO POSE DATA CAPTURED. Check camera and lighting."
        print(f"[PERCEPTION] {error_msg}")
        return {
            **state,
            "error": error_msg,
            "status": "error",
            "next_action": "end"
        }

    laban_scores = _compute_laban_scores(frame_data)
    dominant = max(laban_scores, key=laban_scores.get)
    confidence = laban_scores[dominant]

    print(f"\n[PERCEPTION] ✓ REAL DATA CAPTURED")
    print(f"  Frames: {len(frame_data)}")
    print(f"  Dominant: {dominant} ({confidence:.1%})")
    print(f"  Camera: {camera_index}")
    print(f"  Scores: {laban_scores}\n")

    return {
        **state,
        "session_id": session_id,
        "raw_landmarks": frame_data,
        "laban_scores": laban_scores,
        "dominant_movement": dominant,
        "movement_confidence": confidence,
        "status": "running",
        "next_action": "reasoning"
    }
