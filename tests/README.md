# Tests - Diagnostic Scripts

All diagnostic scripts for testing wallet, contract, and blockchain connectivity.

## Quick Start

```bash
# Run all tests
python tests/test_wallet.py
python tests/test_contract.py
python tests/test_owner.py
```

## What Each Test Does

### `test_wallet.py`
- ✅ Validates private key format
- ✅ Derives wallet address
- ✅ Checks RPC connection to Sepolia
- ✅ Verifies wallet has sufficient ETH balance
- ✅ Fetches transaction nonce

**What to look for**: "✅ WALLET READY FOR MINTING!"

### `test_contract.py`
- ✅ Validates contract address format
- ✅ Confirms contract is deployed (has bytecode)
- ✅ Builds a dummy mint transaction
- ✅ Estimates gas
- ✅ Signs transaction

**What to look for**: "✅ CONTRACT IS READY TO MINT!"

### `test_owner.py`
- ✅ Calls contract.owner() function
- ✅ Compares returned owner with wallet address
- ✅ Confirms wallet can call onlyOwner functions

**What to look for**: "✅ WALLET IS OWNER - Can mint!"

## When to Run

1. **Before any deployment**: Ensures local environment is correct
2. **After changing wallet/contract in .env**: Verify configuration
3. **When debugging blockchain failures**: Identifies what's broken
4. **First thing when onboarding**: Validates setup

## Requirements

```bash
pip install web3
```

## Interpreting Errors

| Error | Meaning | Fix |
|-------|---------|-----|
| `WALLET_PRIVATE_KEY is EMPTY` | Env var not set | Set in .env or Vercel dashboard |
| `RPC connection failed` | Can't reach Sepolia | Check internet, RPC endpoint |
| `LOW BALANCE` | Less than 0.001 ETH | Get Sepolia ETH from faucet |
| `NO CONTRACT CODE` | Contract not deployed | Deploy contract first |
| `WALLET IS NOT OWNER` | Wrong private key | Use owner's private key |

## Extending Tests

To add new tests, create `test_feature.py` in this directory following the same pattern:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ...  # Import what you need
```

Remember to update `sys.path.insert()` to go up one level to reach config.py
