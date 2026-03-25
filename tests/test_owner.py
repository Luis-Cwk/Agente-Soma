#!/usr/bin/env python3
"""
Check if wallet is contract owner
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
print("OWNER CHECK")
print("=" * 60)

w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)

print(f"\nWallet address: {account.address}")
print(f"Contract:      {NFT_CONTRACT_ADDRESS}")

# Check code at contract address
code = w3.eth.get_code(Web3.to_checksum_address(NFT_CONTRACT_ADDRESS))
print(f"Contract deployed: {'✓' if code != '0x' else '✗'}")

# Try to call owner() function
try:
    contract_abi = [
        {
            "name": "owner",
            "type": "function",
            "inputs": [],
            "outputs": [{"type": "address"}],
            "stateMutability": "view"
        }
    ]
    
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(NFT_CONTRACT_ADDRESS),
        abi=contract_abi
    )
    
    owner = contract.functions.owner().call()
    print(f"\nContract owner: {owner}")
    
    if owner.lower() == account.address.lower():
        print("✅ WALLET IS OWNER - Can mint!")
    else:
        print(f"❌ WALLET IS NOT OWNER")
        print(f"   Your wallet:  {account.address}")
        print(f"   Contract owner: {owner}")
        
except Exception as e:
    print(f"Could not read owner(): {e}")
