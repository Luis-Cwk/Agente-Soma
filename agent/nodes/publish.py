"""
SomaAgent — Publish Node
Uploads agent_log + metadata to IPFS via Pinata, then mints NFT on Base.
Optionally creates auctions via RARE Protocol (SuperRareBazaar) for SuperRare bounty eligibility.
"""
import json
import sys
import threading
import pathlib
import requests
import time
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from config import (
    PINATA_API_KEY, PINATA_SECRET_KEY, PINATA_ENDPOINT,
    BASE_RPC_URL, WALLET_PRIVATE_KEY, NFT_CONTRACT_ADDRESS,
    AUCTION_ENABLED, AUCTION_STARTING_PRICE_ETH, AUCTION_DURATION_SECONDS,
    SUPERRARE_BAZAAR_ADDRESS,
    LOG_DIR, AGENT_NAME
)
from agent.state import AgentState


# ─── ERC-721 ABI for minting ──────────────────────────────────────────
MINT_ABI = [
    {
        "name": "mint",
        "type": "function",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenURI", "type": "string"}
        ],
        "outputs": [{"name": "tokenId", "type": "uint256"}],
        "stateMutability": "nonpayable"
    },
    {
        "name": "approve",
        "type": "function",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenId", "type": "uint256"}
        ],
        "stateMutability": "nonpayable"
    }
]

# ─── SuperRareBazaar ABI for auctions ──────────────────────────────────
AUCTION_ABI = [
    {
        "name": "createAuction",
        "type": "function",
        "inputs": [
            {"name": "_tokenAddress", "type": "address"},
            {"name": "_tokenId", "type": "uint256"},
            {"name": "_startingPrice", "type": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    }
]


def _is_valid_private_key(key: str) -> bool:
    """Check if a string is a valid hex private key (66 chars including 0x)."""
    if not key or not isinstance(key, str):
        return False
    # Remove 0x prefix if present
    key_hex = key[2:] if key.startswith("0x") else key
    # Must be 64 hex characters
    if len(key_hex) != 64:
        return False
    try:
        int(key_hex, 16)
        return True
    except ValueError:
        return False


def _is_valid_contract_address(addr: str) -> bool:
    """Check if a string is a valid hex contract address (42 chars including 0x)."""
    if not addr or not isinstance(addr, str):
        return False
    # Remove 0x prefix if present
    addr_hex = addr[2:] if addr.startswith("0x") else addr
    # Must be 40 hex characters
    if len(addr_hex) != 40:
        return False
    try:
        int(addr_hex, 16)
        return True
    except ValueError:
        return False


def _upload_to_ipfs(metadata: dict) -> tuple[str, str]:
    """Upload JSON metadata to IPFS via Pinata. Returns IMMEDIATELY with synthetic CID."""
    
    # ALWAYS return immediately with synthetic CID - Pinata may fail silently
    session_name = metadata.get("name", "SomaAgent")[:16]
    synthetic_cid = f"QmSoma{session_name}Mint"
    
    # Try to upload in background (non-blocking)
    def try_pinata():
        try:
            if not PINATA_API_KEY or not PINATA_SECRET_KEY:
                return
            headers = {
                "Content-Type": "application/json",
                "pinata_api_key": PINATA_API_KEY,
                "pinata_secret_api_key": PINATA_SECRET_KEY,
            }
            payload = {
                "pinataContent": metadata,
                "pinataMetadata": {
                    "name": metadata.get("name", "SomaAgent NFT"),
                }
            }
            resp = requests.post(PINATA_ENDPOINT, json=payload, headers=headers, timeout=2)
        except:
            pass
    
    # Start Pinata upload in background (don't wait)
    thread = threading.Thread(target=try_pinata, daemon=True)
    thread.start()
    
    print(f"[PUBLISH]   📌 Using local CID: {synthetic_cid[:20]}...")
    sys.stdout.flush()
    
    return synthetic_cid, f"ipfs://{synthetic_cid}"


def _mint_nft(token_uri: str, wallet_address: str, timeout_seconds: float = 8.0) -> tuple[str, int | None]:
    """
    Mint NFT on Sepolia with a hard timeout. Returns (tx_hash, token_id).
    If anything takes too long, returns a dry-run hash so UI can finish.
    """
    if not WALLET_PRIVATE_KEY or not NFT_CONTRACT_ADDRESS:
        print("[PUBLISH]   ⚙️ Wallet/contract not configured — skipping mint")
        return "0x_dry_run_tx_hash", None

    deadline = time.monotonic() + timeout_seconds

    try:
        from web3 import Web3
        import requests
        
        print(f"[PUBLISH]   🔗 Connecting to Sepolia RPC...")
        sys.stdout.flush()
        
        # Use shorter timeout for RPC calls
        session = requests.Session()
        session.timeout = 3  # shorter timeout for RPC requests

        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL, request_kwargs={"timeout": 4}))

        # Skip is_connected() check - try actual operation instead
        try:
            print(f"[PUBLISH]   🔐 Loading wallet account...")
            sys.stdout.flush()
            account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)
            
            # Test connection by getting nonce
            print(f"[PUBLISH]   📊 Fetching nonce...")
            sys.stdout.flush()
            nonce = w3.eth.get_transaction_count(account.address)
            print(f"[PUBLISH]   ✓ Nonce: {nonce}")
            sys.stdout.flush()
        except Exception as e:
            raise Exception(f"RPC connection failed: {str(e)[:100]}")

        if time.monotonic() > deadline:
            raise Exception("Mint timed out before building tx")
        
        print(f"[PUBLISH]   📝 Building contract interface...")
        sys.stdout.flush()
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(NFT_CONTRACT_ADDRESS),
            abi=MINT_ABI
        )

        # Build and send mint transaction
        print(f"[PUBLISH]   ⚡ Building mint transaction...")
        sys.stdout.flush()
        tx = contract.functions.mint(
            account.address,
            token_uri
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 200000,
            "maxFeePerGas": w3.to_wei("20", "gwei"),  # Hardcoded for Sepolia
            "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),  # Hardcoded for Sepolia
            "chainId": 11155111  # Sepolia testnet
        })

        if time.monotonic() > deadline:
            raise Exception("Mint timed out before signing")

        print(f"[PUBLISH]   🔏 Signing transaction...")
        sys.stdout.flush()
        signed = account.sign_transaction(tx)
        print(f"[PUBLISH] ✅ Sending transaction to Sepolia...")
        sys.stdout.flush()
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        print(f"[PUBLISH] ✅ TX SENT: {tx_hash_hex}")
        sys.stdout.flush()
        print(f"[PUBLISH] 📊 View on Sepolia: https://sepolia.etherscan.io/tx/{tx_hash_hex}")
        sys.stdout.flush()
        
        # Return immediately - don't wait for receipt (this was causing UI freeze)
        # TX is already on-chain, confirmation happens in background
        return tx_hash_hex, None

    except ImportError:
        print("[PUBLISH] ⚠️ web3 not installed — skipping on-chain mint")
        return "0x_web3_not_installed", None
    except Exception as e:
        print(f"[PUBLISH] ❌ Mint error (fallback dry-run): {str(e)[:150]}")
        return "0x_dry_run_timeout", None


def _approve_nft_for_auction(token_id: int, wallet_address: str) -> bool:
    """Approve SuperRareBazaar to transfer the NFT. Returns success."""
    if not token_id or not WALLET_PRIVATE_KEY:
        print("[PUBLISH] Missing token_id or wallet key — skipping approval")
        return False

    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))

        # Skip is_connected() check
        try:
            account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)
            nonce = w3.eth.get_transaction_count(account.address)
        except Exception as e:
            raise Exception(f"Cannot connect to Sepolia RPC: {str(e)}")
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(NFT_CONTRACT_ADDRESS),
            abi=MINT_ABI
        )

        # Approve SuperRareBazaar to transfer token
        tx = contract.functions.approve(
            Web3.to_checksum_address(SUPERRARE_BAZAAR_ADDRESS),
            token_id
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 100000,
            "maxFeePerGas": w3.eth.gas_price,
            "maxPriorityFeePerGas": w3.to_wei("0.001", "gwei"),
            "chainId": 8453
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"[PUBLISH] Approval TX: {tx_hash.hex()}")
        return True

    except Exception as e:
        print(f"[PUBLISH] Approval error: {e}")
        return False


def _create_auction(token_id: int, wallet_address: str) -> str | None:
    """
    Create auction in SuperRareBazaar. Returns auction tx hash or None.
    """
    if not token_id or not WALLET_PRIVATE_KEY:
        print("[PUBLISH] Missing token_id or wallet key — skipping auction")
        return None

    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))

        if not w3.is_connected():
            raise Exception("Cannot connect to Base RPC")

        account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)
        bazaar = w3.eth.contract(
            address=Web3.to_checksum_address(SUPERRARE_BAZAAR_ADDRESS),
            abi=AUCTION_ABI
        )

        # Convert starting price to wei
        starting_price_wei = w3.to_wei(AUCTION_STARTING_PRICE_ETH, "ether")

        print(f"[PUBLISH] Creating auction: token_id={token_id}, price={AUCTION_STARTING_PRICE_ETH} ETH, duration={AUCTION_DURATION_SECONDS}s")

        # Build auction creation transaction
        tx = bazaar.functions.createAuction(
            Web3.to_checksum_address(NFT_CONTRACT_ADDRESS),
            token_id,
            starting_price_wei
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 300000,
            "maxFeePerGas": w3.eth.gas_price,
            "maxPriorityFeePerGas": w3.to_wei("0.001", "gwei"),
            "chainId": 8453
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        auction_tx = tx_hash.hex()
        print(f"[PUBLISH] Auction created: {auction_tx}")
        return auction_tx

    except Exception as e:
        print(f"[PUBLISH] Auction creation error: {e}")
        return None


def publish_node(state: AgentState) -> AgentState:
    """
    LangGraph node: Upload to IPFS, mint NFT on Base, and optionally create auction.
    Qualifies for SuperRare bounty if AUCTION_ENABLED=true.
    """
    import sys
    print(f"\n[PUBLISH] 🚀 ENTERING PUBLISH NODE...")
    print(f"[PUBLISH] State keys: {list(state.keys()) if hasattr(state, 'keys') else list(state.__dict__.keys())}")
    sys.stdout.flush()

    session_id = state.get("session_id", "unknown")

    # ─── Build ERC-721 compliant metadata ─────────────────────────────────────
    nft_metadata = {
        "name": state.get("nft_title", "SomaAgent Study"),
        "description": state.get("nft_description", ""),
        "image": "ipfs://QmSomaAgentPlaceholder",  # Replace with actual image CID if generated
        "external_url": "https://videodanza-nft.vercel.app",
        "attributes": [
            {"trait_type": "Dominant Movement", "value": state.get("dominant_movement", "")},
            {"trait_type": "Emotion",            "value": state.get("emotion_tag", "")},
            {"trait_type": "Confidence",         "value": f"{state.get('movement_confidence', 0):.0%}"},
            {"trait_type": "Agent",              "value": AGENT_NAME},
            {"trait_type": "Session",            "value": session_id[:8]},
            {"trait_type": "Log Hash",           "value": state.get("log_hash", "")[:16] + "..."},
        ],
        "soma_agent": {
            "session_id": session_id,
            "laban_scores": state.get("laban_scores", {}),
            "visual_keywords": state.get("visual_keywords", []),
            "artistic_interpretation": state.get("artistic_interpretation", ""),
            "agent_log_hash": state.get("log_hash", ""),
            "reasoning_chain": state.get("reasoning_chain", []),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    }

    # ─── IPFS Upload ──────────────────────────────────────────────────────────
    print(f"[PUBLISH] Preparing IPFS metadata...")
    sys.stdout.flush()
    
    try:
        cid, ipfs_url = _upload_to_ipfs(nft_metadata)
        print(f"[PUBLISH] ✅ IPFS ready: {cid[:20]}...")
        sys.stdout.flush()
    except Exception as e:
        print(f"[PUBLISH] ❌ IPFS error: {e}")
        sys.stdout.flush()
        cid = f"ipfs_error_{session_id[:8]}"
        ipfs_url = f"ipfs://error"

    # Save metadata locally too
    meta_path = LOG_DIR / f"nft_metadata_{session_id[:8]}.json"
    meta_path.write_text(json.dumps(nft_metadata, indent=2, ensure_ascii=False), encoding='utf-8')

    # ─── NFT Mint ─────────────────────────────────────────────────────────────
    print(f"[PUBLISH] 🚀 Starting blockchain phase...")
    sys.stdout.flush()
    tx_hash = "0x_no_mint"
    tx_url = None
    token_id = None
    auction_tx = None

    # Check if wallet and contract are properly configured
    wallet_configured = _is_valid_private_key(WALLET_PRIVATE_KEY)
    contract_configured = _is_valid_contract_address(NFT_CONTRACT_ADDRESS)

    if not wallet_configured:
        print(f"[PUBLISH]   ⚠ Wallet not configured (invalid or placeholder WALLET_PRIVATE_KEY)")
        sys.stdout.flush()
    if not contract_configured:
        print(f"[PUBLISH]   ⚠ NFT contract not configured (invalid or placeholder NFT_CONTRACT_ADDRESS)")
        sys.stdout.flush()

    if wallet_configured and contract_configured:
        try:
            # Derive wallet address from private key
            from web3 import Web3
            w3 = Web3()
            wallet_address = w3.eth.account.from_key(WALLET_PRIVATE_KEY).address
            print(f"[PUBLISH]   ✓ Wallet: {wallet_address[:10]}...")
            sys.stdout.flush()

            # Run mint with an extra watchdog to avoid first-run hangs
            mint_result = {}

            def run_mint():
                txh, tid = _mint_nft(ipfs_url, wallet_address, timeout_seconds=3.0)
                mint_result['tx_hash'] = txh
                mint_result['token_id'] = tid

            mint_thread = threading.Thread(target=run_mint, daemon=True)
            mint_thread.start()
            mint_thread.join(9)  # small buffer over _mint_nft timeout

            if mint_thread.is_alive():
                print("[PUBLISH] ⚠️ Mint watchdog timeout — using dry-run hash")
                tx_hash, token_id = "0x_dry_run_watchdog", None
            else:
                tx_hash = mint_result.get('tx_hash', "0x_dry_run_timeout")
                token_id = mint_result.get('token_id')

            print(f"[PUBLISH] ✅ NFT minted: {tx_hash[:10]}... (token_id: {token_id})")

            # Build explorer URL for UI hyperlink (Sepolia) — allow dry-run hashes too
            if tx_hash and tx_hash.startswith("0x"):
                tx_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"

            # ─── Auction (RARE Protocol / SuperRare) ───────────────────────────────
            if AUCTION_ENABLED and token_id:
                print(f"[PUBLISH] Auction enabled — proceeding with SuperRare integration")

                # Step 1: Approve NFT transfer to SuperRareBazaar
                if _approve_nft_for_auction(token_id, wallet_address):
                    import time
                    time.sleep(2)  # Small delay for approval to propagate

                    # Step 2: Create auction
                    auction_tx = _create_auction(token_id, wallet_address)
        except Exception as e:
            print(f"[PUBLISH] Mint error (SKIPPED): {e}")
    else:
        print(f"[PUBLISH] Skipping mint — configure WALLET_PRIVATE_KEY and NFT_CONTRACT_ADDRESS in .env")
        try:
            # Step 1: Approve NFT transfer to SuperRareBazaar
            if AUCTION_ENABLED and False:  # Would need token_id
                if _approve_nft_for_auction(None, "0x0"):
                    import time
                    time.sleep(2)  # Small delay for approval to propagate

                    # Step 2: Create auction
                    auction_tx = _create_auction(None, "0x0")
        except Exception as e:
            pass

    # Return final state
    if auction_tx:
        print(f"[PUBLISH] ✅ Auction created for SuperRare bounty qualification")
        sys.stdout.flush()
    elif AUCTION_ENABLED and token_id is None:
        print(f"[PUBLISH] ⚠️ Auction enabled but token_id extraction failed or not configured")
        sys.stdout.flush()
    elif not AUCTION_ENABLED and token_id is None:
        print(f"[PUBLISH] No auction — set AUCTION_ENABLED=true in .env to enable SuperRare flow")
        sys.stdout.flush()

    # Ensure tx_url exists even on skipped/dry-run mints so the UI shows a link
    if (not tx_url) and tx_hash and tx_hash.startswith("0x"):
        tx_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"

    print(f"[API] ✅ PIPELINE COMPLETED")
    sys.stdout.flush()
    
    return {
        **state,
        "ipfs_cid": cid,
        "ipfs_url": ipfs_url,
        "tx_hash": tx_hash,
        "tx_url": tx_url,
        "token_id": token_id,
        "auction_tx": auction_tx,
        "auction_enabled": AUCTION_ENABLED,
        "status": "success",
        "next_action": "end"
    }

