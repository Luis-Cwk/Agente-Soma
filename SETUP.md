# SomaAgent v2 — Installation & Setup Guide

## Prerequisites

- **Python 3.10+** (download from [python.org](https://www.python.org))
- **Webcam/Camera** (for motion capture)
- **Internet connection** (for blockchain & IPFS)
- **Git** (for cloning)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/SomaAgent-v2.git
cd SomaAgent-v2
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**Required Configuration:**

```env
# Ollama Cloud API (LLM)
OLLAMA_BASE_URL=https://api.ollama.com
OLLAMA_API_KEY=your_api_key_here
OLLAMA_MODEL=glm-5

# Pinata IPFS
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret

# Sepolia Blockchain (Testnet)
BASE_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
WALLET_PRIVATE_KEY=your_wallet_private_key
NFT_CONTRACT_ADDRESS=0x3D1A31542D49b1759FBD1861991D1D6742C8d340
```

#### Getting API Keys:

**Ollama Cloud:**
1. Go to [https://ollama.com](https://ollama.com)
2. Create account & get API key
3. Model: `glm-5` (recommended, fast + accurate)

**Pinata IPFS:**
1. Go to [https://pinata.cloud](https://pinata.cloud)
2. Sign up free
3. Get API key & secret from dashboard

**Sepolia Wallet:**
1. Import wallet to MetaMask
2. Private key: Export from MetaMask (⚠️ NEVER share)
3. Request testnet ETH from [Sepolia Faucet](https://www.sepoliafaucet.io)

## Running

### Start Flask Server

```bash
python -u app.py
```

Server starts at: **http://localhost:5000**

### Web Interface

1. Open http://localhost:5000 in browser
2. Click **▶ START CAPTURE**
3. Move for 15 seconds (or custom duration)
4. Watch real-time pipeline execution
5. View NFT metadata, IPFS link, transaction hash

## Pipeline Overview

```
📷 PERCEPTION (MediaPipe)
    ↓
📊 LABAN ANALYSIS (8 movement efforts)
    ↓
💡 REASONING (LLM interpretation)
    ↓
🏗️ LOGGING (ERC-8004 hash chain)
    ↓
📍 IPFS UPLOAD (Pinata)
    ↓
⛓️ BLOCKCHAIN MINT (Sepolia testnet)
```

## Troubleshooting

### Camera Not Found
- Ensure camera is connected
- Try: `python test_camera.py` to debug

### Ollama Timeout
- LLM defaults to prewritten metadata if slow
- No error - pipeline continues

### Sepolia RPC Error
- Use PublicNode RPC: `https://ethereum-sepolia-rpc.publicnode.com`
- Request testnet ETH: [Sepolia Faucet](https://www.sepoliafaucet.io)

### IPFS Upload Fails
- Check Pinata account balance
- Verify API key in `.env`

## Features

✅ Real-time motion capture (MediaPipe)  
✅ Laban movement classification (8 efforts)  
✅ AI-generated artistic titles (Ollama LLM)  
✅ Distributed storage (Pinata IPFS)  
✅ Blockchain verification (Sepolia ERC-721)  
✅ Hash chain logging (ERC-8004)  
✅ Web dashboard with live updates  

## Next Steps

- Deploy to production (Docker recommended)
- Connect to mainnet (Base/Ethereum)
- Enable auctions (SuperRare integration)

## Support

Issues? Check logs in `logs/` directory or open an issue on GitHub.
