import json
import os
from web3 import Web3
from pathlib import Path

# ABI file paths
CURRENT_DIR = Path(__file__).parent.absolute()
ABI_DIR = CURRENT_DIR / "abi"

# Load ABIs
with open(ABI_DIR / "WeightedTreasuryVault.json") as f:
    VAULT_ABI = json.load(f)

with open(ABI_DIR / "UniAdapter.json") as f:
    ADAPTER_ABI = json.load(f)

with open(ABI_DIR / "UniTwapOracle.json") as f:
    ORACLE_ABI = json.load(f)

with open(ABI_DIR / "ERC20.json") as f:
    ERC20_ABI = json.load(f)

# Chain config
NETWORKS = {
    "base": {
        "rpc_url": "https://mainnet.base.org",
        "chain_id": 8453,
        "explorer": "https://basescan.org",
        "name": "Base Mainnet"
    },
    "base_sepolia": {
        "rpc_url": "https://sepolia.base.org",
        "chain_id": 84532,
        "explorer": "https://sepolia.basescan.org",
        "name": "Base Sepolia Testnet"
    }
}

# Default to Base Mainnet
DEFAULT_NETWORK = "base"

def get_web3(network: str = DEFAULT_NETWORK):
    """Get Web3 instance for the specified network"""
    if network not in NETWORKS:
        raise ValueError(f"Unknown network: {network}")
    
    # Use environment variable if set, otherwise use default
    rpc_url = os.environ.get(f"WR_TREASURY_{network.upper()}_RPC", 
                             NETWORKS[network]["rpc_url"])
    
    return Web3(Web3.HTTPProvider(rpc_url))