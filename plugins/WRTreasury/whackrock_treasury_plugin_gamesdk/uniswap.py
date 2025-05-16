import requests
import time
import logging
from typing import List, Dict, Any, Union, Optional
from web3 import Web3

from .config import (
    UNIVERSAL_ROUTER, 
    BASE_CHAIN_ID, 
    UNISWAP_ROUTER_API, 
    DEFAULT_SLIPPAGE_BPS, 
    DEFAULT_TOKENS
)
from .utils import logger

def resolve_token(token: str) -> str:
    """
    Resolve token from symbol or address
    
    Args:
        token: Token symbol (e.g., 'ETH') or address
        
    Returns:
        Token address
    """
    if token in DEFAULT_TOKENS:
        return DEFAULT_TOKENS[token]
    return Web3.to_checksum_address(token)

def build_swap_calldata(
    vault_addr: str, 
    sells: List[Dict[str, Any]], 
    buys: List[Dict[str, Any]], 
    max_slip_bps: int = DEFAULT_SLIPPAGE_BPS,
    retry_count: int = 3
) -> bytes:
    """
    Build Uniswap swap calldata for rebalancing
    
    Args:
        vault_addr: Address of the vault (not used in current implementation)
        sells: List of assets to sell, each as {"token": address, "amt": wei_amount}
        buys: List of assets to buy, each as {"token": address, "amt": wei_amount}
        max_slip_bps: Maximum slippage in basis points (e.g., 30 = 0.3%)
        retry_count: Number of retries on API failure
        
    Returns:
        Encoded swap calldata for the rebalance function
        
    Raises:
        ValueError: If API request fails or returns invalid data
    """
    if not sells or not buys:
        raise ValueError("At least one sell and one buy asset required")
    
    # Handle token resolution (allow symbols or addresses)
    src = sells[0].copy()  # Create a copy to avoid modifying the original
    dst = buys[0].copy()
    
    # Resolve token addresses if symbols were provided
    src["token"] = resolve_token(src["token"])
    dst["token"] = resolve_token(dst["token"])
    
    # Build the query string
    query_params = {
        "tokenIn": src["token"],
        "tokenOut": dst["token"],
        "amount": src["amt"],
        "type": "exactIn",
        "chainId": BASE_CHAIN_ID,
        "slippageToleranceBps": max_slip_bps
    }
    
    # Convert to query string
    query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
    
    # Make request with retries
    last_error = None
    for attempt in range(retry_count):
        try:
            logger.debug(f"Making Uniswap API request (attempt {attempt+1}/{retry_count})")
            response = requests.get(f"{UNISWAP_ROUTER_API}?{query_string}", timeout=10)
            response.raise_for_status()  # Raise exception for non-200 responses
            
            quote_data = response.json()
            if "methodParameters" not in quote_data or "calldata" not in quote_data["methodParameters"]:
                raise ValueError(f"Invalid response from Uniswap API: {quote_data}")
            
            logger.info(f"Swap quote received: {src['token']} → {dst['token']}")
            logger.debug(f"Quote data: {quote_data}")
            return quote_data["methodParameters"]["calldata"]
            
        except (requests.RequestException, ValueError) as e:
            last_error = str(e)
            logger.warning(f"Uniswap API request failed (attempt {attempt+1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                # Exponential backoff
                time.sleep(1 * 2**attempt)
    
    # If we get here, all retries failed
    raise ValueError(f"Failed to get swap quote after {retry_count} attempts: {last_error}")

def estimate_swap_price(sell_token: str, buy_token: str, sell_amount: int) -> Dict[str, Any]:
    """
    Estimate the price for a swap without executing it
    
    Args:
        sell_token: Token to sell (symbol or address)
        buy_token: Token to buy (symbol or address)
        sell_amount: Amount of sell_token in wei
        
    Returns:
        Dictionary with price information
    """
    # Resolve token addresses
    sell_token = resolve_token(sell_token)
    buy_token = resolve_token(buy_token)
    
    logger.info(f"Estimating swap: {sell_amount} of {sell_token} → {buy_token}")
    
    # Build query string
    query_params = {
        "tokenIn": sell_token,
        "tokenOut": buy_token,
        "amount": sell_amount,
        "type": "exactIn",
        "chainId": BASE_CHAIN_ID
    }
    
    # Convert to query string
    query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
    
    try:
        response = requests.get(f"{UNISWAP_ROUTER_API}?{query_string}", timeout=10)
        response.raise_for_status()
        quote_data = response.json()
        
        # Extract and return relevant information
        result = {
            "sell_token": sell_token,
            "buy_token": buy_token,
            "sell_amount": sell_amount,
            "buy_amount": int(quote_data.get("quote", 0)),
            "price_impact": float(quote_data.get("priceImpact", 0)) if "priceImpact" in quote_data else None,
            "gas_estimate": int(quote_data.get("gasUseEstimate", 0)) if "gasUseEstimate" in quote_data else None
        }
        
        logger.debug(f"Swap estimate result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to estimate swap price: {e}")
        raise ValueError(f"Failed to estimate swap price: {e}")
