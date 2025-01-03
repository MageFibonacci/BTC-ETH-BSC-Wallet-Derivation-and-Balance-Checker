from mnemonic import Mnemonic
from bip_utils import Bip44, Bip44Coins, Bip44Changes, Bip84, Bip84Coins
import os
import datetime
import requests
import concurrent.futures
import time

# Initialize the BIP-39 seed generator
mnemo = Mnemonic("english")

# variable
logging = 0  # Set to 1 to enable debug ApiCall logging, 0 to disable it
mode = 3  # For future use
bsc_api_key = 'XXXXXXXXXXXXXXX'  # Replace with your BscScan API key
eth_api_key = 'XXXXXXXXXXXXXXX'  # Replace with your Etherscan API key


# Function to generate standards-compliant entropy
def generate_valid_seed_phrase():
    entropy = os.urandom(16)  # 16 byte = 128 bit
    seed_phrase = mnemo.to_mnemonic(entropy)
    return seed_phrase

# Function to derive Ethereum address from a seed phrase
def derive_eth_address(seed_phrase, index=0):
    seed_bytes = mnemo.to_seed(seed_phrase)
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    return bip44_acc.PublicKey().ToAddress()

# Function to derive traditional Bitcoin address from a seed phrase
def derive_btc_address(seed_phrase, index=0):
    seed_bytes = mnemo.to_seed(seed_phrase)
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    return bip44_acc.PublicKey().ToAddress()

# Function to derive SegWit address (Bech32) from a seed phrase
def derive_segwit_btc_address(seed_phrase, index=0):
    seed_bytes = mnemo.to_seed(seed_phrase)
    bip84_mst = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)  # Use BIP-84 for SegWit
    bip84_acc = bip84_mst.Purpose().Coin().Account(0)  # Fixed: Flows correctly in the hierarchy
    bip84_ext = bip84_acc.Change(Bip44Changes.CHAIN_EXT)  # Outside (public)
    bip84_addr = bip84_ext.AddressIndex(index)  # We derive the address from the BIP-84 path
    return bip84_addr.PublicKey().ToAddress()

# Function to get the private key in HEX format
def derive_private_key_hex(seed_phrase, coin_type=Bip44Coins.BITCOIN, index=0):
    seed_bytes = mnemo.to_seed(seed_phrase)
    bip44_mst = Bip44.FromSeed(seed_bytes, coin_type)
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    return bip44_acc.PrivateKey().Raw().ToHex()

# Function to format balances, handling numeric values and 'NOT_RETRIEVE'
def format_balance(balance):
    if isinstance(balance, float):  # If the balance is a number (float)
        return f"{balance:.8f}"
    else:  # If the balance is 'NOT_RETRIEVE' or another string type
        return balance

# Function to get balance of BTC addresses (traditional and SegWit) in batch
def get_batch_btc_balance(addresses):
    addresses_str = "|".join(addresses)
    
    # Call to BlockChain for Traditional BTC and SegWit
    url = f"https://blockchain.info/balance?active={addresses_str}&cors=true"
    response = requests.get(url)
    
    # Perform logging if the logging variable is set to 1
    if logging == 1:
        with open("btc_apicall_log.txt", "a") as log_file:
            log_file.write(f"URL: {url}\n")
            log_file.write(f"Status Code: {response.status_code}\n")
            log_file.write("Response Body:\n")
            log_file.write(response.text + "\n")
            log_file.write("=" * 50 + "\n")  # Separator for clarity between requests
    
    if response.status_code == 200:
        balances = response.json()
        return {address: balances.get(address, {}).get("final_balance", 0) / 1e8 for address in addresses}
    else:
        return {address: "NOT_RETRIEVE" for address in addresses}
        

# Function to get Ethereum address balance using BscScan and Etherscan
def get_batch_eth_balance(addresses):
    addresses_str = ",".join(addresses)

    # Call to BscScan
    bsc_url = f"https://api.bscscan.com/api?module=account&action=balancemulti&address={addresses_str}&tag=latest&apikey={bsc_api_key}"
    bsc_response = requests.get(bsc_url)
    
    # Perform logging if the logging variable is set to 1
    if logging == 1:
        with open("bsc_apicall_log.txt", "a") as log_file:
            log_file.write(f"URL: {bsc_url}\n")
            log_file.write(f"Status Code: {bsc_response.status_code}\n")
            log_file.write("Response Body:\n")
            log_file.write(bsc_response.text + "\n")
            log_file.write("=" * 50 + "\n")  # Separator for clarity between requests
            
    bsc_balances = {}
    if bsc_response.status_code == 200:
        bsc_data = bsc_response.json()
        if bsc_data['status'] == '1':
            for result in bsc_data['result']:
                bsc_balances[result['account']] = int(result['balance']) / 1e18
        else:
            for address in addresses:
                bsc_balances[address] = "NOT_RETRIEVE"
    else:
        for address in addresses:
            bsc_balances[address] = "NOT_RETRIEVE"

    # Call to Etherscan
    eth_url = f"https://api.etherscan.io/api?module=account&action=balancemulti&address={addresses_str}&tag=latest&apikey={eth_api_key}"
    eth_response = requests.get(eth_url)
    
    # Perform logging if the logging variable is set to 1
    if logging == 1:
        with open("eth_apicall_log.txt", "a") as log_file:
            log_file.write(f"URL: {eth_url}\n")
            log_file.write(f"Status Code: {eth_response.status_code}\n")
            log_file.write("Response Body:\n")
            log_file.write(eth_response.text + "\n")
            log_file.write("=" * 50 + "\n")  # Separator for clarity between requests
            
    eth_balances = {}
    if eth_response.status_code == 200:
        eth_data = eth_response.json()
        if eth_data['status'] == '1':
            for result in eth_data['result']:
                eth_balances[result['account']] = int(result['balance']) / 1e18
        else:
            for address in addresses:
                eth_balances[address] = "NOT_RETRIEVE"
    else:
        for address in addresses:
            eth_balances[address] = "NOT_RETRIEVE"

    return bsc_balances, eth_balances

def log_attempt(seed_phrase, private_key_hex, eth_address, btc_address, btc_segwit_address, bsc_balance, eth_balance, btc_balance, btc_segwit_balance):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       
    # Formatting balances
    bsc_balance_formatted = format_balance(bsc_balance)
    eth_balance_formatted = format_balance(eth_balance)
    btc_balance_formatted = format_balance(btc_balance)
    btc_segwit_balance_formatted = format_balance(btc_segwit_balance)

    with open("ethbtc_seed.txt", "a") as log_file:
        log_file.write(f"Date: {current_time}, Seed Phrase: {seed_phrase}, Private Key HEX: {private_key_hex}, ETH Address: {eth_address}, BTC Address: {btc_address}, BTC SegWit Address: {btc_segwit_address}, BSC Balance: {bsc_balance_formatted} BNB, ETH Balance: {eth_balance_formatted} ETH, BTC Balance: {btc_balance_formatted} BTC, BTC SegWit Balance: {btc_segwit_balance_formatted} BTC\n")


# Function to save Ethereum address log
def log_wallet_address(eth_address):
    with open("ethbsc_wallets.txt", "a") as eth_log:
        eth_log.write(f"{eth_address}\n")

# Function to save log of traditional Bitcoin addresses
def log_btc_wallet_address(btc_address):
    with open("btc_wallets.txt", "a") as btc_log:
        btc_log.write(f"{btc_address}\n")

# Function to save SegWit address log
def log_segwit_btc_wallet_address(btc_segwit_address):
    with open("btcsegwit_wallets.txt", "a") as segwit_log:
        segwit_log.write(f"{btc_segwit_address}\n")
        
# Function to save the "jackpot" log for addresses with positive balance
def log_jackpot(seed_phrase, private_key_hex, eth_address, btc_address, btc_segwit_address, bsc_balance, eth_balance, btc_balance, btc_segwit_balance):
    
    # Check if there are positive balances
    if (isinstance(bsc_balance, float) and bsc_balance > 0) or \
       (isinstance(eth_balance, float) and eth_balance > 0) or \
       (isinstance(btc_balance, float) and btc_balance > 0) or \
       (isinstance(btc_segwit_balance, float) and btc_segwit_balance > 0):
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format balances before writing to file or printing
        bsc_balance_formatted = format_balance(bsc_balance)
        eth_balance_formatted = format_balance(eth_balance)
        btc_balance_formatted = format_balance(btc_balance)
        btc_segwit_balance_formatted = format_balance(btc_segwit_balance)

        # Write to the file "jackpot.txt"
        with open("jackpot.txt", "a") as jackpot_log:
            jackpot_log.write(f"Date: {current_time}, Seed Phrase: {seed_phrase}, Private Key HEX: {private_key_hex}, ETH Address: {eth_address}, BTC Address: {btc_address}, BTC SegWit Address: {btc_segwit_address}, BSC Balance: {bsc_balance_formatted} BNB, ETH Balance: {eth_balance_formatted} ETH, BTC Balance: {btc_balance_formatted} BTC, BTC SegWit Balance: {btc_segwit_balance_formatted} BTC\n")
        
        # Print to console if positive balance is found
        print(f"JACKPOT FOUND!!! Seed Phrase: {seed_phrase}, Private Key HEX: {private_key_hex}, ETH Address: {eth_address}, BTC Address: {btc_address}, BTC SegWit Address: {btc_segwit_address}, BSC Balance: {bsc_balance_formatted} BNB, ETH Balance: {eth_balance_formatted} ETH, BTC Balance: {btc_balance_formatted} BTC, BTC SegWit Balance: {btc_segwit_balance_formatted} BTC")



def generate_and_log_addresses_batch(batch_size=20):
    seed_phrases = [generate_valid_seed_phrase() for _ in range(batch_size)]
    eth_addresses = [derive_eth_address(seed_phrase) for seed_phrase in seed_phrases]
    btc_addresses = [derive_btc_address(seed_phrase) for seed_phrase in seed_phrases]
    btc_segwit_addresses = [derive_segwit_btc_address(seed_phrase) for seed_phrase in seed_phrases]
    private_keys_hex = [derive_private_key_hex(seed_phrase) for seed_phrase in seed_phrases]

    # We get the balances for the generated addresses
    bsc_balances, eth_balances = get_batch_eth_balance(eth_addresses)
    btc_balances = get_batch_btc_balance(btc_addresses + btc_segwit_addresses)

    # Log all results
    for i in range(batch_size):
        seed_phrase = seed_phrases[i]
        eth_address = eth_addresses[i]
        btc_address = btc_addresses[i]
        btc_segwit_address = btc_segwit_addresses[i]
        private_key_hex = private_keys_hex[i]

        eth_balance = eth_balances.get(eth_address, "NOT_RETRIEVE")
        bsc_balance = bsc_balances.get(eth_address, "NOT_RETRIEVE")
        btc_balance = btc_balances.get(btc_address, "NOT_RETRIEVE")
        btc_segwit_balance = btc_balances.get(btc_segwit_address, "NOT_RETRIEVE")

        # Formatting balances
        eth_balance_formatted = format_balance(eth_balance)
        bsc_balance_formatted = format_balance(bsc_balance)
        btc_balance_formatted = format_balance(btc_balance)
        btc_segwit_balance_formatted = format_balance(btc_segwit_balance)

        print("---------")
        print(f"Seed: {seed_phrase}")
        print(f"Private Key HEX: {private_key_hex}")
        print(f"ETH/BSC Wallet: {eth_address}")
        print(f"BTC Wallet: {btc_address}")
        print(f"BTC SegWit Wallet: {btc_segwit_address}")
        print(f"BSC Balance: {bsc_balance_formatted} BNB")
        print(f"ETH Balance: {eth_balance_formatted} ETH")
        print(f"BTC Balance: {btc_balance_formatted} BTC")
        print(f"BTC SegWit Balance: {btc_segwit_balance_formatted} BTC")
        print("---------")

        # Save logs
        log_attempt(seed_phrase, private_key_hex, eth_address, btc_address, btc_segwit_address, bsc_balance_formatted, eth_balance_formatted, btc_balance_formatted, btc_segwit_balance_formatted)
        log_wallet_address(eth_address)
        log_btc_wallet_address(btc_address)
        log_segwit_btc_wallet_address(btc_segwit_address)

        # Save log for jackpot
        log_jackpot(seed_phrase, private_key_hex, eth_address, btc_address, btc_segwit_address, bsc_balance_formatted, eth_balance_formatted, btc_balance_formatted, btc_segwit_balance_formatted)
        

# Run the script according to the mode
if mode == 3:
    while True:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(generate_and_log_addresses_batch) for _ in range(4)]
            concurrent.futures.wait(futures)
        time.sleep(1)

