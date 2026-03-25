# SomaAgent NFT Minting — Tests, Verifications & Proofs Explained

## 🎓 Three Different Things (Understand the Difference)

### 1️⃣ TESTS (What to check LOCALLY before deployment)
**Purpose**: Verify your local environment is ready

```
TEST: Wallet Diagnostics
├─ Question: "Can I connect to the blockchain?"
├─ Script: python tests/test_wallet.py
├─ Checks:
│  ├─ Private key format is valid (64 hex chars)
│  ├─ Can derive wallet address from private key
│  ├─ RPC connection works (can reach Sepolia)
│  ├─ Wallet has ETH balance (for gas)
│  └─ Can fetch nonce (prove connection is real)
└─ Result: ✅ Wallet ready OR ❌ Fix config

TEST: Contract Callable
├─ Question: "Is the smart contract deployed correctly?"
├─ Script: python tests/test_contract.py
├─ Checks:
│  ├─ Contract code exists at address
│  ├─ Can build a mint transaction
│  ├─ Can sign with wallet
│  └─ Gas estimation works
└─ Result: ✅ Contract ready OR ❌ Contract not deployed

TEST: Ownership
├─ Question: "Does my wallet own the contract?"
├─ Script: python tests/test_owner.py
├─ Checks:
│  ├─ Contract.owner() returns wallet address
│  └─ Wallet matches your WALLET_PRIVATE_KEY
└─ Result: ✅ Can call onlyOwner functions OR ❌ Not owner
```

**Timeline**: ~30 seconds total
**Rule**: Run BEFORE every deployment

---

### 2️⃣ VERIFICATION (What to check AFTER deployment)
**Purpose**: Confirm code reached blockchain without crashing

```
VERIFICATION: Endpoint Responds
├─ Action: POST to Vercel function
├─ Check: Got HTTP 200 response
├─ What it proves: Vercel didn't timeout/crash
└─ Result: Response JSON received

VERIFICATION: Logs Show Progress
├─ Action: Look at Vercel logs for [publish] lines
├─ Timeline of logs:
│  ├─ [publish] Starting...
│  ├─ [publish] IPFS success: Qm...
│  ├─ [publish] Creating wallet...
│  ├─ [publish] Nonce: 41
│  ├─ [publish] Calling mint(...)
│  └─ [publish] ❌ MINT ERROR: X (if failed)
│  └─ [publish] ✅ TX SENT: 0x... (if worked)
├─ What it proves: Code reached each step
└─ Key metric: Where does it stop?

VERIFICATION: Response Contains Valid Data
├─ Check response JSON for:
│  ├─ ipfs_cid: "Qm..." (exists ✅)
│  ├─ tx_hash: "0x..." (real hash, not null/pending ✅)
│  └─ tx_url: "https://sepolia.etherscan.io/tx/0x..."
├─ What it proves: Function completed successfully
└─ Red flags:
   ├─ tx_hash: null = Mint failed silently
   ├─ tx_hash: "pending_mint_..." = Fallback (error caught)
   ├─ tx_url: null = No transaction link
```

**Timeline**: ~2-3 minutes after deployment (wait for Vercel rebuild)
**Rule**: Always check logs on failures

---

### 3️⃣ PROOFS (What to check ON THE BLOCKCHAIN)
**Purpose**: Completely verify something actually happened on-chain

```
PROOF: Transaction Exists
├─ Action: Visit Sepolia Explorer
├─ URL: https://sepolia.etherscan.io/tx/{tx_hash}
├─ Look for:
│  ├─ Status: ✅ Success (green)
│  ├─ From: Your wallet address
│  ├─ To: Contract address
│  ├─ Gas Used: > 0 (proves execution)
│  ├─ Input Data: 0x40d0... (the mint call)
│  └─ Logs: Event emitted (token created)
├─ What it proves: Real transaction on real blockchain
└─ Immutable: Saved forever on Sepolia

PROOF: NFT Minted
├─ Check contract on explorer:
│  ├─ Address: 0x3D1A31542D49b1759...
│  ├─ Name: SomaArt
│  ├─ Token Count: +1 from before
│  └─ Owner: Your wallet address
├─ What it proves: NFT actually created
└─ Verification: Can view on marketplaces

PROOF: Metadata Stored
├─ Visit IPFS gateway:
│  ├─ URL: https://gateway.pinata.cloud/ipfs/{CID}
│  ├─ Check: JSON metadata visible
│  ├─ Contains: name, description, attributes
│  └─ Points to: IPFS artwork/video
├─ What it proves: Metadata was really uploaded
└─ Durability: Permanent on IPFS
```

**Timeline**: ~1 minute to explorer + ~1 minute to verify
**Rule**: Never trust without proof on chain

---

## 📋 The Complete Workflow

```
START
  │
  ├─→ RUN LOCAL TESTS (5 min)
  │   ├─ python tests/test_wallet.py ────→ ✅ Balance check
  │   ├─ python tests/test_contract.py ──→ ✅ Gas estimation
  │   └─ python tests/test_owner.py ─────→ ✅ Ownership
  │
  ├─→ CODE REVIEW (2 min)
  │   └─ Check publish.js for obvious issues
  │
  ├─→ PUSH TO GITHUB (1 min)
  │   └─ git add/commit/push → Vercel auto-deploys
  │
  ├─→ WAIT FOR VERCEL BUILD (1-2 min)
  │   └─ Watch: https://vercel.com/Luis-Cwk/SomaAgent
  │
  ├─→ TEST ON VERCEL (2 min)
  │   ├─ Open https://skill-deploy-...vercel.app/
  │   ├─ Trigger publish (dance capture or button)
  │   └─ Check browser console (F12 → Console)
  │
  ├─→ VERIFY LOGS (2 min) [IF FAILED]
  │   ├─ Vercel dashboard → Deployments → Logs
  │   ├─ Look for [publish] lines
  │   └─ Find error message: "X is not a function" etc
  │
  ├─→ PROOF ON EXPLORER (2 min) [IF WORKED]
  │   ├─ Copy tx_hash from browser
  │   ├─ Go to sepolia.etherscan.io
  │   ├─ Paste hash → Search
  │   └─ Verify: Status=Success, Gas used > 0
  │
  └─→ DONE ✅
```

**Total time**: ~15 minutes (with retries, maybe 30-45 min)

---

## 🔍 Decision Tree: "Why Didn't It Work?"

```
tx_hash: null ?
├─ YES → [publish] ❌ MINT ERROR in logs?
│         ├─ YES → "provider.X is not a function"?
│         │         ├─ YES → Ethers v5 vs v6 issue
│         │         └─ NO → Check specific error
│         └─ NO → logs don't show starting blockchain?
│                 ├─ YES → IPFS wrong, env vars missing
│                 └─ NO → Function crashed silently
└─ NO (is "0x...") → Real tx hash!
                     ├─ tx_url exists? 
                     │  └─ YES → Click it, verify on explorer
                     └─ NO → Bug in response formatting
```

---

## ✅ Success Criteria

| Item | Success Looks Like |
|------|------------------|
| **Test Phase** | All 3 scripts return ✅ |
| **Verification Phase** | Browser shows `✅ Publish success:` with real tx_hash |
| **Proof Phase** | Sepolia explorer shows: Status ✅, Gas Used > 0, Event logs |

---

## 🚀 Ready for Next Agent

This document explains:
- ✅ What each test does
- ✅ What each verification checks
- ✅ What counts as real proof
- ✅ The complete workflow
- ✅ How to debug when things fail

**Save this file** for any future blockchain debugging.
