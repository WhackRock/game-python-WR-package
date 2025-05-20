"""
Configuration settings for WhackRock Treasury Plugin
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Network Configuration
BASE_CHAIN_ID = 8453
BASE_TESTNET_CHAIN_ID = 84532

# Smart Contract Addresses
UNIVERSAL_ROUTER = "0x3fC91a3AFd70395cD496c647D5A6cC9D4b2B7Fad"  # Base Mainnet
FACTORY_ADDRESS = "0x23b6928d90aD8766Cb3BD546205934e010C3E746"  # WhackRockTreasuryFactory
ORACLE_ADDRESS = "0x91E9F29E1a7282E1e66471BB13e1e53D0a898101"  # UniTwapOracle
ADAPTER_ADDRESS = "0xC2B12b66b4d2022778e59D60b1F476764052d17d"  # UniAdapter

# Default tokens that can be referenced by name
DEFAULT_TOKENS = {
    "ETH": "0x0000000000000000000000000000000000000000",  # Native ETH
    "WETH": "0x4200000000000000000000000000000000000006",  # Wrapped ETH on Base
    "USDCb": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USD Coin on Base (updated)
    "VIRTUALS": "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b",  # Virtuals token
    "UNKNOWN": "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",  # Unknown token
    "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",  # DAI on Base
    "USDT": "0x7076377bd7b951687DAEC0FAaA0CB451188E8D3C",  # Tether on Base
}

# Environment variable configuration 
def get_env(key: str, default: Optional[str] = None) -> str:
    """Get environment variable with fallback to default"""
    return os.environ.get(key, default)

def get_rpc_url(testnet: bool = False) -> str:
    """Get the RPC URL for Base network
    
    Args:
        testnet: Whether to use testnet RPC URL
        
    Returns:
        RPC URL string
    """
    if testnet:
        return get_env("BASE_TESTNET_RPC", "https://sepolia.base.org")
    return get_env("BASE_RPC", "https://mainnet.base.org")

# Get default vault address from environment
DEFAULT_VAULT_ADDRESS = get_env("TREASURY_VAULT_ADDRESS")

# External service URLs
UNISWAP_ROUTER_API = "https://router.uniswap.org/quote"

# Default slippage settings from environment or fallbacks
DEFAULT_SLIPPAGE_BPS = int(get_env("DEFAULT_SLIPPAGE_BPS", "30"))  # Default: 0.3%
MAX_SLIPPAGE_BPS = 200  # Hard limit: 2%

# Rebalance threshold from environment or fallback
REBALANCE_THRESHOLD_BPS = int(get_env("REBALANCE_THRESHOLD_BPS", "200"))  # Default: 2%

# Configure logging level
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")

# ABI snippets for common interactions
VAULT_ABI_SNIPPET = [
    {
        "inputs": [],
        "name": "targetWeights",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256[]", "name": "w", "type": "uint256[]"}],
        "name": "setWeights",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes", "name": "data", "type": "bytes"}],
        "name": "rebalance",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

ORACLE_ABI_SNIPPET = [
    {
        "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
        "name": "usdPrice",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
] 