# BTC and ETH Wallet Derivation and Balance Checker

This script generates Bitcoin (BTC) and Ethereum (ETH) wallet addresses using BIP-44 derivation paths, checks balances via APIs, and logs results.

## Features
- Generates mnemonic seed phrases (BIP-39 compliant).
- Derives BTC (`m/44'/0'/0'/0`) and ETH wallet addresses.
- Derives BTC SegWit (Bech32) wallet addresses.
- Extracts private keys in HEX format.
- Checks BTC balances via Blockchain.info (batch requests supported).
- Checks ETH and BSC balances via Etherscan and BscScan APIs.
- Logs:
  - All seed phrases, addresses, private keys, and balances.
  - Non-zero balances ("jackpot" detection).
- Supports batch processing and multi-threaded execution.

## Outputs
- `ethbsc_wallets.txt`: Ethereum wallet addresses.
- `btc_wallets.txt`: Bitcoin wallet addresses.
- `ethbtc_seed.txt`: Seed phrases, addresses, private keys, and balances.
- `jackpot.txt`: Non-zero balance addresses.

## Requirements
- Python 3.8+
- Dependencies: bip_utils, mnemonic, requests, concurrent.futures
- Etherscan and BscScan Api Key (Free Plan)

## Performance
- Checking 60 Addresses per second

## Usage
1. Clone repository.
2. Install dependencies.
3. Run script: `python ethbscbtc.py`.
