"""
Simple Asset Allocation Strategy

This module implements a basic strategy that:
1. Gets prices from the Uniswap oracle
2. Allocates 70% to the best-performing asset (stETH or WBTC)
3. Keeps 30% in USDT as a stable buffer

You can replace this with your own strategy logic.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional
from decimal import Decimal

from web3 import Web3, AsyncWeb3
from whackrock_treasury_plugin_gamesdk import resolve_token_address
from whackrock_treasury_plugin_gamesdk.config import get_env, get_rpc_url

# Setup logger
logger = logging.getLogger("treasury_signals")

# Configuration from environment or defaults
ORACLE_ADDRESS = get_env("ORACLE_ADDRESS", "0xORACLE")  # Oracle contract address

# You can use token symbols or addresses (from env or defaults)
TOKENS = {
    "stETH": get_env("stETH", "0xSTETH"),   # Liquid staked ETH
    "WBTC": get_env("WBTC", "0xWBTC"),      # Wrapped Bitcoin
    "USDT": get_env("USDT", "USDT")         # Tether stablecoin
}

# Log token configuration
for symbol, address in TOKENS.items():
    logger.info(f"Using token {symbol}: {address}")

# Get RPC URL from environment
RPC_URL = get_rpc_url()
logger.info(f"Using RPC URL: {RPC_URL}")

# Set up Web3 client
try:
    W3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))
    logger.info("Web3 client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Web3: {e}")
    raise

# Contract ABI (only the function we need)
ORACLE_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
        "name": "usdPrice", 
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Initialize oracle contract
oracle = W3.eth.contract(address=ORACLE_ADDRESS, abi=ORACLE_ABI)
logger.info(f"Oracle contract initialized at {ORACLE_ADDRESS}")

async def get_price(token_address: str) -> Decimal:
    """
    Get the USD price of a token from the oracle
    
    Args:
        token_address: Address of the token
        
    Returns:
        Price in USD as a Decimal
    """
    try:
        # Ensure the address is in checksum format
        token_address = Web3.to_checksum_address(token_address)
        logger.debug(f"Getting price for {token_address}")
        price = await oracle.functions.usdPrice(token_address).call()
        logger.debug(f"Received price: {price}")
        return Decimal(price)
    except Exception as e:
        logger.error(f"Failed to get price for {token_address}: {e}")
        # Return 0 instead of failing - your strategy might handle this differently
        return Decimal('0')

async def get_all_prices() -> Dict[str, Decimal]:
    """
    Get prices for all tokens in the strategy
    
    Returns:
        Dictionary mapping token symbols to USD prices
    """
    prices = {}
    
    for symbol, address in TOKENS.items():
        # Resolve the address if it's a symbol
        resolved_address = resolve_token_address(address)
        logger.debug(f"Resolving {symbol} ({address}) to {resolved_address}")
        price = await get_price(resolved_address)
        prices[symbol] = price
        logger.info(f"Price of {symbol}: ${price}")
    
    return prices

async def derive_weights() -> List[float]:
    """
    Derive target weights based on price performance
    
    This simple strategy:
    1. Allocates 70% to the best performing of stETH or WBTC
    2. Keeps 30% in USDT as a stable buffer
    
    Returns:
        List of weights in percentage (0-1) matching the order of TOKENS dict
    """
    try:
        logger.info("Deriving target weights based on price performance")
        
        # Get prices
        prices = await get_all_prices()
        
        # Simple strategy: allocate to highest price
        if prices["stETH"] > prices["WBTC"]:
            logger.info(f"stETH outperforming WBTC ({prices['stETH']} > {prices['WBTC']}), allocating 70% to stETH")
            return [0.70, 0.00, 0.30]  # 70% stETH, 0% WBTC, 30% USDT
        else:
            logger.info(f"WBTC outperforming stETH ({prices['WBTC']} >= {prices['stETH']}), allocating 70% to WBTC")
            return [0.00, 0.70, 0.30]  # 0% stETH, 70% WBTC, 30% USDT
    except Exception as e:
        logger.error(f"Strategy calculation failed: {e}")
        # Fallback to a safe allocation if there's an error
        logger.warning("Falling back to 100% stable allocation due to error")
        return [0.00, 0.00, 1.00]  # 100% stable in case of error

# Allow running the module directly for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running signal generator in standalone mode")
    weights = asyncio.run(derive_weights())
    print(f"Target weights: {weights}")
    print(f"Sum of weights: {sum(weights)}")  # Should equal 1.0
