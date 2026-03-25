#!/usr/bin/env python3
"""
Test if the NFT contract is callable and can build transactions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import WALLET_PRIVATE_KEY, BASE_RPC_URL, NFT_CONTRACT_ADDRESS

try:
    from web3 import Web3
except ImportError:
    print("❌ web3.py not installed")
    sys.exit(1)

print("=" * 60)
print("CONTRACT CALLABLE TEST")
print("=" * 60)

# Check contract address
print("\n1️⃣  CONTRACT ADDRESS VALIDATION")
if not NFT_CONTRACT_ADDRESS:
    print("   ❌ NFT_CONTRACT_ADDRESS is EMPTY in .env")
    sys.exit(1)

addr_hex = NFT_CONTRACT_ADDRESS[2:] if NFT_CONTRACT_ADDRESS.startswith("0x") else NFT_CONTRACT_ADDRESS
if len(addr_hex) != 40:
    print(f"   ❌ Invalid format (length={len(addr_hex)}, expected 40)")
    sys.exit(1)

print(f"   Address: {NFT_CONTRACT_ADDRESS}")
print("   ✓ Format valid")

# Connect to RPC
print("\n2️⃣  CONNECTING TO SEPOLIA RPC")
w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL, request_kwargs={"timeout": 5}))
account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)
print(f"   Connected as: {account.address}")

# Check if contract exists
print("\n3️⃣  CHECKING CONTRACT DEPLOYMENT")
try:
    code = w3.eth.get_code(Web3.to_checksum_address(NFT_CONTRACT_ADDRESS))
    if code == "0x":
        print(f"   ❌ NO CONTRACT CODE at {NFT_CONTRACT_ADDRESS}")
        print(f"   Check: https://sepolia.etherscan.io/address/{NFT_CONTRACT_ADDRESS}")
        sys.exit(1)
    print(f"   ✓ Contract deployed ({len(code)} bytes)")
except Exception as e:
    print(f"   ❌ Error checking contract: {e}")
    sys.exit(1)

# Try to build a mint transaction
print("\n4️⃣  BUILDING MINT TRANSACTION")
try:
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
        }
    ]
    
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(NFT_CONTRACT_ADDRESS),
        abi=MINT_ABI
    )
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = contract.functions.mint(
        account.address,
        "ipfs://QmTestURI"
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 150000,
        "maxFeePerGas": gas_price,
        "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
        "chainId": 11155111
    })
    
    print(f"   ✓ Transaction built successfully")
    print(f"   Gas estimate: {tx['gas']} units")
    print(f"   Max fee: {w3.from_wei(tx['maxFeePerGas'], 'gwei'):.2f} gwei")
    
except Exception as e:
    print(f"   ❌ Error building transaction: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to sign
print("\n5️⃣  SIGNING TRANSACTION")
try:
    signed = account.sign_transaction(tx)
    print(f"   ✓ Signed successfully")
    print(f"   TX hash hex: {signed.hash.hex()}")
except Exception as e:
    print(f"   ❌ Error signing transaction: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ CONTRACT IS READY TO MINT!")
print("=" * 60)
print("\nNext steps:")
print("1. Deploy to Vercel with: git push")
print("2. Test on https://skill-deploy-o8dmn73huw.vercel.app/")
print("3. Check Vercel logs if it still fails")
