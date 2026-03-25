#!/usr/bin/env python3
"""
Quick wallet diagnostic - Check if your wallet has Sepolia ETH
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import WALLET_PRIVATE_KEY, BASE_RPC_URL

try:
    from web3 import Web3
except ImportError:
    print("❌ web3.py not installed. Run: pip install web3")
    sys.exit(1)

print("=" * 60)
print("WALLET DIAGNOSTIC TEST")
print("=" * 60)

# 1. Check private key format
print("\n1️⃣  PRIVATE KEY VALIDATION")
if not WALLET_PRIVATE_KEY:
    print("   ❌ WALLET_PRIVATE_KEY is EMPTY in .env")
    sys.exit(1)

key_hex = WALLET_PRIVATE_KEY[2:] if WALLET_PRIVATE_KEY.startswith("0x") else WALLET_PRIVATE_KEY
if len(key_hex) != 64:
    print(f"   ❌ Invalid format (length={len(key_hex)}, expected 64)")
    sys.exit(1)

print("   ✓ Format valid (64 hex chars)")

# 2. Derive wallet address
print("\n2️⃣  DERIVING WALLET ADDRESS")
w3 = Web3()
account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)
print(f"   Address: {account.address}")

# 3. Connect to RPC
print("\n3️⃣  CONNECTING TO SEPOLIA RPC")
print(f"   Endpoint: {BASE_RPC_URL[:50]}...")

try:
    w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL, request_kwargs={"timeout": 5}))
    chain_id = w3.eth.chain_id
    print(f"   ✓ Connected (Chain ID: {chain_id})")
except Exception as e:
    print(f"   ❌ RPC connection failed: {e}")
    sys.exit(1)

# 4. Check balance
print("\n4️⃣  CHECKING BALANCE")
try:
    balance_wei = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance_wei, "ether")
    print(f"   Balance: {balance_eth:.6f} ETH")
    
    if balance_eth < 0.001:
        print(f"   ⚠️  LOW BALANCE! Need at least 0.001 ETH for gas")
        print(f"   Get Sepolia ETH from: https://www.sepoliafaucet.com")
    else:
        print(f"   ✓ Sufficient balance")
except Exception as e:
    print(f"   ❌ Failed to check balance: {e}")
    sys.exit(1)

# 5. Check nonce
print("\n5️⃣  CHECKING NONCE")
try:
    nonce = w3.eth.get_transaction_count(account.address)
    print(f"   Nonce: {nonce}")
    print("   ✓ RPC responding normally")
except Exception as e:
    print(f"   ❌ Failed to get nonce: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ WALLET READY FOR MINTING!")
print("=" * 60)
