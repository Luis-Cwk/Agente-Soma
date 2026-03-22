"""
SomaAgent v2 — Web Frontend + Backend
Flask server with WebSocket support for real-time agent interaction.
"""
import os
import sys
import json
import time
import threading
import logging
from pathlib import Path
from datetime import datetime
from queue import Queue, Empty

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import cv2

# ─── Disable Flask HTTP Logging (reduce console noise) ──────────────────
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ─── Constants ─────────────────────────────────────────────────────────
MAX_LOGS = 500

# ─── Log Capture ───────────────────────────────────────────────────────
class LogCapture:
    """Capture print() statements globally"""
    def __init__(self):
        self.terminal = None
        self.lines = []
    
    def write(self, msg):
        if msg and msg.strip():
            self.lines.append(msg.strip())
            if len(self.lines) > MAX_LOGS:
                self.lines.pop(0)
        if self.terminal:
            self.terminal.write(msg)
    
    def flush(self):
        if self.terminal:
            self.terminal.flush()

# Import SomaAgent components
sys.path.insert(0, str(Path(__file__).parent))
from agent.graph import build_graph
from agent.state import AgentState
from config import LOG_DIR, AGENT_NAME, AGENT_VERSION, CAMERA_INDEX

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Global state
agent_graph = build_graph()
current_session = None
capture_thread = None
capture_start_time = None
current_session_id = None
log_capture = LogCapture()  # ← Real-time log capture

# Redirect stdout to capture logs
log_capture.terminal = sys.stdout
sys.stdout = log_capture


@app.route('/')
def index():
    """Serve the main UI."""
    return render_template('index.html')





@app.route('/api/agent/info')
def agent_info():
    """Get agent information."""
    return jsonify({
        'name': AGENT_NAME,
        'version': AGENT_VERSION,
        'status': 'ready',
        'pipeline': ['perception', 'reasoning', 'logging', 'publishing'],
        'models': {
            'perception': 'MediaPipe Pose',
            'reasoning': 'glm-5:cloud (Ollama)',
            'logging': 'ERC-8004 v1',
            'publishing': 'IPFS + Base NFT'
        }
    })


@app.route('/api/agent/reset', methods=['POST'])
def reset_agent():
    """Reset the agent state for a new capture."""
    global current_session, current_session_id
    current_session = None
    current_session_id = None
    return jsonify({'status': 'reset_complete'})


@app.route('/api/agent/start-capture', methods=['POST'])
def start_capture():
    """
    Start a capture session using the default camera.
    """
    global current_session, capture_thread, capture_start_time, current_session_id

    # Clear in-memory live logs so the UI starts fresh and stays in sync
    log_capture.lines = []
    
    # Reset state for new capture
    import uuid
    new_session_id = str(uuid.uuid4())
    current_session_id = new_session_id
    capture_start_time = time.time()
    
    # Set initial running state
    current_session = {
        'session_id': new_session_id,
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'elapsed': 0,
        'data': {}
    }
    
    duration = request.json.get('duration', 15)
    
    def run_capture():
        global current_session, current_session_id
        
        try:
            # Initialize state
            state = AgentState(
                session_id=None,
                raw_landmarks=None,
                laban_scores=None,
                dominant_movement=None,
                movement_confidence=None,
                reasoning_chain=None,
                artistic_interpretation=None,
                nft_title=None,
                nft_description=None,
                visual_keywords=None,
                emotion_tag=None,
                log_entries=None,
                log_hash=None,
                prev_log_hash=None,
                ipfs_cid=None,
                ipfs_url=None,
                tx_hash=None,
                token_id=None,
                auction_tx=None,
                auction_enabled=None,
                error=None,
                status='running',
                next_action='perception'
            )
            
            print(f"[API] Starting capture: {duration}s on default camera {CAMERA_INDEX}")
            
            # Create config dict for the graph - MUST be wrapped in "configurable" for LangGraph
            config = {
                "configurable": {
                    'capture_seconds': duration
                }
            }
            
            # Run graph in a worker thread with a hard timeout to avoid first-run hangs
            print("[API] ✅ RUNNING PIPELINE...")
            result_q: Queue = Queue()

            def run_graph():
                try:
                    result_q.put(agent_graph.invoke(state, config=config))
                except Exception as e:
                    print(f"[API] ✗ Pipeline error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    result_q.put(state)

            worker = threading.Thread(target=run_graph, daemon=True)
            worker.start()

            # Timeout: capture duration + 10s buffer
            timeout_seconds = duration + 10
            worker.join(timeout_seconds)

            if worker.is_alive():
                print("[API] ⚠️ Pipeline timeout — returning fallback state to unblock UI")
                final_state = {
                    **state,
                    "status": "timeout",
                    "next_action": "end",
                    "tx_hash": "0x_timeout",
                    "tx_url": "https://sepolia.etherscan.io/tx/0x_timeout"
                }
            else:
                final_state = result_q.get() if not result_q.empty() else state
                print("[API] ✅ PIPELINE COMPLETED")
            
            # Convert to dict for easier access (handle both dict and dataclass)
            if hasattr(final_state, '__dict__'):
                state_dict = final_state.__dict__
            else:
                state_dict = final_state if isinstance(final_state, dict) else {}
            
            print(f"[API] Pipeline complete, marking status COMPLETE...")
            
            # Prepare response data - mark as complete
            current_session = {
                'session_id': current_session_id,
                'status': 'complete',  # ← Mark complete IMMEDIATELY
                'timestamp': datetime.now().isoformat(),
                'elapsed': time.time() - capture_start_time,
                'capture_session_id': state_dict.get('session_id', 'unknown'),
                'current_node': 'complete',
                'data': {
                    'movement': state_dict.get('dominant_movement'),
                    'confidence': float(state_dict.get('movement_confidence', 0) or 0),
                    'laban_scores': state_dict.get('laban_scores') or {},
                    'emotion': state_dict.get('emotion_tag'),
                    'nft_title': state_dict.get('nft_title'),
                    'nft_description': state_dict.get('nft_description'),
                    'keywords': state_dict.get('visual_keywords') or [],
                    'ipfs': state_dict.get('ipfs_url'),
                    'tx_hash': state_dict.get('tx_hash'),
                    'tx_url': state_dict.get('tx_url') or (state_dict.get('tx_hash') and f"https://sepolia.etherscan.io/tx/{state_dict.get('tx_hash')}") or None,
                    'log_hash': state_dict.get('log_hash'),
                    'prev_log_hash': state_dict.get('prev_log_hash')
                }
            }
            print(f"[API] Capture complete: {current_session['session_id']}")
            
        except Exception as e:
            print(f"[API] Capture error: {e}")
            import traceback
            traceback.print_exc()
            current_session = {
                'session_id': current_session_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'elapsed': time.time() - capture_start_time
            }
        finally:
            pass
    
    # Start capture in background thread
    capture_thread = threading.Thread(target=run_capture, daemon=True)
    capture_thread.start()
    
    return jsonify({
        'status': 'started',
        'duration': duration,
        'message': f'Capturing for {duration} seconds...'
    })


@app.route('/api/agent/session', methods=['GET'])
def get_session():
    """Get current session results."""
    if current_session is None:
        return jsonify({
            'status': 'idle',
            'session_id': None,
            'data': None,
            'message': 'No active session. Click START CAPTURE to begin.'
        })
    return jsonify(current_session)


@app.route('/api/agent/reset-session', methods=['POST'])
def reset_session():
    """Reset session state (call on page load or before new capture)."""
    global current_session
    current_session = None
    return jsonify({
        'status': 'idle',
        'message': 'Session reset. Ready for new capture.'
    })


@app.route('/api/agent/logs', methods=['GET'])
def get_logs():
    """Get real-time + historical logs.
    
    Returns:
        - real_time: Current capture logs (last 100 lines)
        - historical: Saved log files from LOG_DIR
    """
    # Real-time logs from current capture
    real_time_logs = log_capture.lines[-50:] if log_capture.lines else []
    
    # Historical logs from files
    log_path = Path(LOG_DIR)
    historical_logs = []
    
    if log_path.exists():
        for log_file in sorted(log_path.glob('agent_log_*.json'), reverse=True)[:10]:
            try:
                with open(log_file) as f:
                    data = json.load(f)
                    historical_logs.append({
                        'filename': log_file.name,
                        'session_id': data.get('session', {}).get('id'),
                        'timestamp': log_file.stat().st_mtime,
                        'entries': len(data.get('entries', []))
                    })
            except:
                pass
    
    return jsonify({
        'real_time': real_time_logs,
        'historical': historical_logs,
        'session_id': current_session_id,
        'timestamp': time.time()
    })


@app.route('/api/agent/logs/<filename>')
def get_log_detail(filename):
    """Get detailed log content."""
    log_file = LOG_DIR / filename
    
    if not log_file.exists():
        return jsonify({'error': 'Not found'}), 404
    
    try:
        with open(log_file) as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check."""
    return jsonify({
        'status': 'healthy',
        'agent': AGENT_NAME,
        'version': AGENT_VERSION,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("🚀 SomaAgent v2 — Web Frontend")
    print(f"📢 Starting at http://localhost:5000")
    print(f"🤖 Agent: {AGENT_NAME} v{AGENT_VERSION}")
    print(f"📷 Using default camera: {CAMERA_INDEX}")
    
    # Disable debug mode and file watcher to prevent server restarts during capture
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
