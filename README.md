# ⬢ SomaAgent

**Autonomous Motion Analysis Agent**

Captures human movement, analyzes Laban effort, generates AI art, and mints NFTs on Sepolia blockchain — all automatically.

> Built for [Synthesis Hackathon 2026](https://synthesis.ai/) | Hackathon Team

---

## 🎯 What It Does

```
📷 PERCEPTION          → 📊 LABAN ANALYSIS      → 💡 REASONING
MediaPipe Keypoints       8-effort classifier       LLM interpretation
(real-time 30fps)        (confidence scores)      (poetic titles & keywords)
       ↓                         ↓                        ↓
⛓️ LOGGING            ← 📍 IPFS UPLOAD        ← 🏆 NFT DECISION
ERC-8004 hash chain    Pinata distributed       Always auto-mint
(cryptographic proof)   storage                  (autonomous = trust)
```

SomaAgent **watches humans move** → **understands how** → **decides what art it becomes** → **mints it as an NFT** ✨

---

## ⚡ Features

✅ **Real-time Motion Capture** (MediaPipe Pose 33 keypoints)  
✅ **Laban Movement Analysis** (8 efforts: punch, float, wring, glide, slash, dab, press, shake)  
✅ **AI-Generated Art Titles** (Ollama Cloud LLM with fallback)  
✅ **Distributed Storage** (Pinata IPFS upload)  
✅ **Blockchain Verification** (Sepolia testnet ERC-721)  
✅ **Hash Chain Logging** (ERC-8004 v1 agent receipt format)  
✅ **Web Dashboard** (live real-time UI at http://localhost:5000)  
✅ **Fully Autonomous** (zero human decisions after start)

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/SomaAgent-v2.git
cd SomaAgent-v2

python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure .env

Copy `.env.example` to `.env` and add:
- **OLLAMA_API_KEY** (from ollama.com)
- **PINATA_API_KEY** & **PINATA_SECRET_KEY** (from pinata.cloud)
- **WALLET_PRIVATE_KEY** (your Sepolia test wallet)
- **BASE_RPC_URL** (Sepolia RPC endpoint)

See **[SETUP.md](SETUP.md)** for detailed instructions.

### 3. Run

```bash
python -u app.py
```

Open **http://localhost:5000** in your browser → Click **▶ START CAPTURE** → Move for 15 seconds → Watch NFT mint! 🎉

---

## 🏗️ Architecture

### LangGraph State Machine

```
STATE
├── session_id: UUID
├── raw_landmarks: MediaPipe frame data
├── laban_scores: {tocar, golpear, flotar, ...}
├── dominant_movement: str (e.g., "sacudir")
├── movement_confidence: float (0.0-1.0)
├── artistic_interpretation: str
├── nft_title: str
├── nft_description: str
├── visual_keywords: [str]
├── emotion_tag: str
├── log_hash: SHA-256
├── prev_log_hash: SHA-256 (chain link)
├── ipfs_cid: str (Pinata CID)
└── tx_hash: str (Sepolia tx)

GRAPH FLOW
perception → reasoning → log → publish → END
```

### Nodes

| Node | Purpose | Tech |
|------|---------|------|
| **Perception** | Capture keypoints + classify Laban efforts | MediaPipe, 8-effort classifier |
| **Reasoning** | Generate NFT metadata + minting decision | Ollama Cloud (glm-5 LLM) |
| **Log** | Create ERC-8004 hash chain entry | SHA-256, JSON |
| **Publish** | Upload to IPFS + mint NFT + record TX | Pinata, Web3.py, Sepolia |

---

## 💾 Project Structure

```
SomaAgent-v2/
├── app.py                      # Flask web server
├── config.py                   # Configuration loader
├── agent/
│   ├── graph.py               # LangGraph state machine
│   ├── state.py               # AgentState dataclass
│   └── nodes/
│       ├── perception.py       # MediaPipe + Laban
│       ├── reasoning.py        # LLM interpretation
│       ├── log_node.py         # ERC-8004 logging
│       └── publish.py          # IPFS + blockchain
├── templates/
│   └── index.html             # Web UI (Tailwind CSS)
├── static/                    # CSS/JS assets
├── logs/                      # Runtime logs (git-ignored)
├── requirements.txt           # Dependencies
├── .env.example               # Configuration template
└── SETUP.md                   # Installation guide
```

---

## 🔗 Blockchain & Storage

| Service | Purpose | Network | Status |
|---------|---------|---------|---------|
| **Sepolia RPC** | Transaction submission | Testnet | ✅ PublicNode |
| **IPFS (Pinata)** | NFT metadata storage | Distributed | ✅ Free tier |
| **ERC-721 Contract** | NFT minting | Sepolia | ✅ 0x3D1A31542D49b1759FBD1861991D1D6742C8d340 |
| **ERC-8004 Logging** | Agent decision logs | JSON chain | ✅ SHA-256 hash |

---

## 📊 Example Flow

**Input:** Human dances for 15 seconds

**Output:**
```json
{
  "movement": "sacudir",
  "confidence": 0.179,
  "laban_scores": {
    "tocar": 0.167,
    "sacudir": 0.179,
    "cortar": 0.162
  },
  "nft_title": "Trembling Energy",
  "nft_description": "Rapid vibrations releasing tension and kinetic power.",
  "keywords": ["vibration", "kinetic", "embodied", "laban"],
  "emotion": "dynamic",
  "ipfs_url": "ipfs://QmUDXMX5nAt4Vy38giLGbBECjcT9ZT6PNq1NAEGFycrjwT",
  "tx_hash": "0xb54296fe43fa45a5f872b4205a854416167bb348c11fc406f1276b96d225c780",
  "log_hash": "0x2f75f3da79e738ca...e846cc1b",
  "prev_log_hash": "0x1f7682b6..."
}
```

View on Sepolia: https://sepolia.etherscan.io/tx/0xb54296fe43fa45a5f872b4205a854416167bb348c11fc406f1276b96d225c780

---

## 🎓 Learning & References

- [Laban Movement Analysis](https://en.wikipedia.org/wiki/Laban_movement_analysis)
- [MediaPipe Pose](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ERC-8004 (Agents With Receipts)](https://erc-8004.example.com)
- [Sepolia Testnet Faucet](https://www.sepoliafaucet.io)

---

## 📝 License

MIT License - See LICENSE file for details

---

```
**Questions?** See [SETUP.md](SETUP.md) for troubleshooting, or open an issue on GitHub.

```
         └──────┬──────────────┬───────┘
                │              │
  ┌─────────────▼───┐    ┌─────▼──────────────┐
  │   LOG NODE       │    │   PUBLISH NODE      │
  │  ERC-8004 v1     │    │  IPFS via Pinata    │
  │  SHA-256 chain   │    │  ERC-721 mint       │
  │  agent_log.json  │    │  Base Mainnet       │
  └─────────────────┘    └─────────────────────┘
```

©2026 Petra. All rights reserved.

### Laban Movement Analysis

8 movement qualities mapped to Effort dimensions:

| Movement | Tiempo | Peso | Espacio | Flujo | Visual Style |
|----------|--------|------|---------|-------|-------------|
| golpear | sudden | strong | direct | bound | explosive geometry, crimson |
| flotar | sustained | light | indirect | free | ethereal particles, lavender |
| deslizar | sustained | light | direct | free | metallic curves, ice blue |
| cortar | sudden | light | indirect | bound | brutalist monochrome |
| presionar | sustained | strong | direct | bound | tectonic pressure, obsidian |
| retorcer | sustained | strong | indirect | bound | bioluminescent spirals |
| sacudir | sudden | light | indirect | free | neon glitch chaos |
| tocar | sudden | strong | indirect | free | pointillism, ink |

---

## 🔒 ERC-8004 Compliance

Every agent session produces a `logs/agent_log_[id].json`:

```json
{
  "schema": "ERC-8004-v1",
  "agent": {
    "name": "SomaAgent",
    "version": "2.0.0",
    "team_id": "874d2679adae49f39a2812e6a66701c6",
    "registration_tx": "0x76b7f88db606c6a6cba0fbd4ed7ee7f36b916587a138b9a518e368d4a66993c0"
  },
  "session": { "id": "...", "pipeline": "perception → reasoning → log → publish" },
  "prev_log_hash": "3d61b13422705b10...",
  "log_hash": "47be4973394af3e7...",
  "entries": [
    {
      "step": 1, "node": "perception",
      "action": "motion_capture",
      "output": { "dominant_movement": "golpear", "confidence": 0.87 },
      "decision": "Detected 'golpear' as primary movement quality",
      "entry_hash": "..."
    },
    {
      "step": 2, "node": "reasoning",
      "action": "artistic_decision",
      "output": { "nft_title": "Crimson Impact, Bound", "emotion_tag": "fury" },
      "decision": "Agent decided to frame movement as 'fury' artwork",
      "entry_hash": "..."
    }
  ]
}
```

**Hash chain**: Each session's `log_hash` becomes the next session's `prev_log_hash`.  
Verified: `00000000 → 3d61b134 → 47be4973 → 6e70c821` ✅

---

## 🚀 Deployment

### Option A: Web Interface (Recommended)

```bash
# 1. Clone
git clone https://github.com/Luis-Cwk/somaagent
cd somaagent

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env: set OLLAMA_API_KEY, PINATA_*, WALLET_PRIVATE_KEY

# 4. Start web server
python app.py

# 5. Open browser
# http://localhost:5000
# - Select camera from 7+ connected
# - Adjust duration
# - Click "START CAPTURE"
# - See real-time results, ERC-8004 hashes, IPFS uploads
```

**Features:**
- ✅ Auto-detects all connected cameras (up to 7)
- ✅ 100% responsive design - works on mobile, tablet, desktop
- ✅ Real-time pipeline visualization
- ✅ Swiss Grid FUI aesthetic
- ✅ Live Laban score bars
- ✅ Hash chain visualization

### Option B: CLI (Headless)

```bash
# Run with camera (default 15 seconds)
python run_auto.py --duration 15

# Dry-run test (no camera needed)
python run_auto.py --dry-run

# Full autonomous mode (auto-saves logs, uploads IPFS, mints NFT)
python run_auto.py --duration 20 --auto-publish
```

---

## 🛠️ Complete Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Orchestration | LangGraph (StateGraph) |
| LLM | glm-5 via Ollama Cloud API |
| Body Capture | MediaPipe Pose (33 landmarks) |
| Movement Analysis | Laban Movement Analysis (8 efforts) |
| Provenance | ERC-8004 SHA-256 hash chain |
| Storage | IPFS via Pinata |
| Blockchain | Base Mainnet, ERC-721 |
| Language | Python 3.11+ |

---

## 🎬 Demo & Resources

**Watch the agent run autonomously:**  
[Video Demo](https://youtu.be/PLACEHOLDER) ← *replace with actual recording*

**Live frontend (NFT viewer):**  
[videodanza-nft.vercel.app](https://videodanza-nft.vercel.app)

**Sample agent log (ERC-8004):**  
[View on IPFS](ipfs://PLACEHOLDER)

---

## 👤 Builder

**Petra / Luis Betancourt**  
[@luisbetx9](https://twitter.com/luisbetx9)  
Wallet: `0x1A49138cCb61C50D72A44a299F6C74c690f6c67f`  
Registration TX: `0x76b7f88db606c6a6cba0fbd4ed7ee7f36b916587a138b9a518e368d4a66993c0`
