# Documentation - Reference & Guides

Comprehensive guides and reference documentation for SomaAgent NFT minting system.

## Files in This Directory

### `TESTS-VERIFICATIONS-PROOFS.md` ⭐ START HERE
**Purpose**: Explains the difference between TESTS, VERIFICATIONS, and PROOFS

Complete workflow guide that explains:
- What each phase of testing does
- Decision tree for debugging
- Success criteria
- Timeline for each step

**Read this first** when onboarding or debugging.

## Documentation Structure

```
docs/
├─ TESTS-VERIFICATIONS-PROOFS.md    ← Workflow guide (main reference)
├─ README.md                         ← This file
└─ [other docs as needed]
```

## Related Documentation

See also:

- **`/memories/repo/SomaAgent-v2-NFT-MINTING-SOLUTION.md`** - Comprehensive technical documentation
  - Full problem/solution breakdown
  - Environment variables required
  - Contract ABI details
  - Troubleshooting matrix
  - Git history of fixes

- **`/memories/blockchain-debugging-workflow.md`** - General blockchain debugging lessons
  - Common pitfalls
  - Debugging strategy
  - Checklist for agents

- **`/memories/session/SomaAgent-NFT-Journey.md`** - Session summary
  - Before/after results
  - Key files changed
  - Quick reference commands

## Quick Links

- **Smart Contract**: `SomaArt.sol` (root directory)
- **Minting Logic**: `api/agent/publish.js`
- **Environment**: `.env` (create from `.env.example`)
- **Tests**: `tests/` directory

## When to Refer to This Doc

1. **Onboarding**: Read `TESTS-VERIFICATIONS-PROOFS.md` first
2. **Debugging**: Use the decision tree in `TESTS-VERIFICATIONS-PROOFS.md`
3. **Understanding flow**: Check memory files for architectural overview
4. **Troubleshooting**: Check Verification section or logs

## Issues & Solutions Covered

This documentation explains how to solve:
- ❌ `tx_hash: null` (root cause: invalid API)
- ❌ Transactions failing silently
- ❌ Ethers.js version incompatibilities
- ❌ RPC connection problems
- ❌ Contract ownership issues
- ❌ Gas estimation failures

All with specific diagnostic tests and verification steps.
