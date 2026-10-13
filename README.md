# Blockchain-Based Tamper-Proof Digital Evidence Locker

A Solidity smart contract on a local Hardhat network that stores the SHA-256 hash of
digital evidence, records every custody handover as an on-chain event, and detects
tampering when a file is re-hashed and compared.

Only the 32-byte hash and metadata go on-chain. The evidence file itself never leaves
the local machine.

## How it works

1. An authorised investigator computes the SHA-256 hash of a file (off-chain, with Node's `crypto`).
2. `registerEvidence` stores the hash, case ID, description, registrant, timestamp and
   current custodian, and emits an `EvidenceRegistered` event.
3. `transferCustody` moves custody to another authorised address and emits a
   `CustodyTransferred` event.
4. `verifyEvidence` compares a freshly computed hash with the stored one. Equal means
   VALID. Different means TAMPERED, even if only one byte changed.
5. The custody history is rebuilt from the events, not from contract storage.

## Contract summary

| Function | Who can call | Purpose |
|---|---|---|
| `setAuthorized(address, bool)` | Owner | Add or remove an authorised investigator |
| `registerEvidence(hash, caseId, description)` | Authorised | Register a file hash, rejects duplicates |
| `transferCustody(id, to)` | Current custodian | Hand evidence to another authorised address |
| `verifyEvidence(id, hash)` | Anyone (view) | Returns true only if the hash matches |
| `getEvidence(id)` | Anyone (view) | Returns the stored record |

## Requirements

- Node.js 22.10 or newer
- git (needed by npm to fetch one dependency)
- Windows PowerShell (commands below), project folder `C:\evidence-locker`

## Setup

```powershell
cd C:\evidence-locker
npm install
npx hardhat build
```

## Run the tests

```powershell
npx hardhat test
```

Expected: 8 passing (registration, unauthorised rejection, duplicate rejection,
valid verification, tamper detection, custody transfer, non-custodian block,
unauthorised recipient block).

## Run the deploy script

```powershell
npx hardhat run scripts/deploy.ts
```

Deploys `EvidenceLocker` to the in-process Hardhat network and authorises two
investigator accounts.

## Run the demo

```powershell
npx hardhat run scripts/demo.ts
```

In one run it creates a sample evidence file, hashes it, registers it, verifies it as
VALID, changes one bit and verifies it as TAMPERED, transfers custody between two
accounts, and prints the custody history from the on-chain events.

To save the output:

```powershell
npx hardhat run scripts/demo.ts | Tee-Object demo-output.txt
```

### Verify a file of your choice

The demo registers its sample file as evidence ID 1. To also check any file against
that record:

```powershell
$env:VERIFY_FILE = "evidence\server-log-tampered.txt"
npx hardhat run scripts/demo.ts
Remove-Item Env:VERIFY_FILE
```

Optionally set `$env:EVIDENCE_ID` to check against a different ID.

You can confirm the hash independently with:

```powershell
Get-FileHash evidence\server-log.txt -Algorithm SHA256
```

## Project structure

```
contracts/EvidenceLocker.sol   the smart contract
test/EvidenceLocker.ts         8 Mocha tests
scripts/deploy.ts              deploy and authorise investigators
scripts/demo.ts                register, verify, tamper demo, custody history
evidence/                      sample files created by the demo (off-chain storage)
```

## Limitations

- The chain proves a file has not changed since registration. It cannot prove the
  evidence was genuine when first collected.
- It runs on a local simulated single-node chain, so there is no real decentralisation
  or consensus across independent parties. The chain is in memory and resets on every
  script run, so registration and verification must happen in the same run.
- Authorisation is a simple allow-list controlled by one owner address.
- Off-chain files live in a normal folder, so deleting a file is not prevented (the
  hash remains, the file is lost).
- Hardhat test accounts are used, with no real wallets or funds.
- A hash mismatch shows that a file differs, not where, how, or by whom it was changed.

## Future scope

Role-based access (admin, investigator, lab, auditor), revocation, a persistent chain
with a verification frontend, wallet-signature login with MetaMask on a test network,
IPFS for file storage, and deployment to a public testnet.
