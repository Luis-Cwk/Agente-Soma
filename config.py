"""
SomaAgent — Configuration
All paths relative. No hardcoded user directories.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root explicitly
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE, verbose=False, override=True)

# ─── Base Paths ───────────────────────────────────────────────
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")
LOG_DIR.mkdir(exist_ok=True)

# ─── LLM (Ollama Cloud) ───────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY  = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "glm-5")

# ─── IPFS / Pinata ────────────────────────────────────────────
PINATA_API_KEY    = os.getenv("PINATA_API_KEY", "")
PINATA_SECRET_KEY = os.getenv("PINATA_SECRET_KEY", "")
PINATA_ENDPOINT   = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

# ─── Blockchain / NFT ─────────────────────────────────────────
BASE_RPC_URL          = os.getenv("BASE_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")
WALLET_PRIVATE_KEY    = os.getenv("WALLET_PRIVATE_KEY", "")
NFT_CONTRACT_ADDRESS  = os.getenv("NFT_CONTRACT_ADDRESS", "")

# ─── Auctions (RARE Protocol / SuperRare) ────────────────────
AUCTION_ENABLED              = os.getenv("AUCTION_ENABLED", "false").lower() == "true"
AUCTION_STARTING_PRICE_ETH   = float(os.getenv("AUCTION_STARTING_PRICE_ETH", "0.05"))
AUCTION_DURATION_SECONDS     = int(os.getenv("AUCTION_DURATION_SECONDS", "86400"))  # 24 hours
SUPERRARE_BAZAAR_ADDRESS     = os.getenv("SUPERRARE_BAZAAR_ADDRESS", "0x51c36ffb05e17ed80ee5c02fa83d7677c5613de2")  # Base

# ─── Agent Identity (ERC-8004) ────────────────────────────────
AGENT_NAME      = os.getenv("AGENT_NAME", "SomaAgent")
AGENT_VERSION   = os.getenv("AGENT_VERSION", "2.0.0")
AGENT_TEAM_ID   = "874d2679adae49f39a2812e6a66701c6"
AGENT_REG_TX    = "0x76b7f88db606c6a6cba0fbd4ed7ee7f36b916587a138b9a518e368d4a66993c0"

# ─── MediaPipe ────────────────────────────────────────────────
CAMERA_INDEX    = int(os.getenv("CAMERA_INDEX", "0"))
CAPTURE_SECONDS = int(os.getenv("CAPTURE_SECONDS", "2"))
MIN_CONFIDENCE  = float(os.getenv("MIN_CONFIDENCE", "0.7"))
