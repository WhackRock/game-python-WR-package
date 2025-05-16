"""
WhackRock Treasury Plugin for GAME SDK

This plugin provides an interface to interact with WhackRock Treasury vaults,
allowing agents to manage asset allocations and execute rebalancing strategies.

Features:
- Get and set asset weights in the vault
- Execute rebalances through Uniswap V3
- Manage portfolio with minimal code
- Support for token symbols (ETH, WETH, USDCb, etc.)
"""

from typing import List, Dict, Any, Optional, Union
from game import game_function

from .treasury import Treasury
from .uniswap import build_swap_calldata, estimate_swap_price, resolve_token
from .config import DEFAULT_TOKENS, DEFAULT_SLIPPAGE_BPS

@game_function(name="get_current_weights")
async def get_current_weights(vault_addr: str) -> List[int]:
    """
    Get the current target weights from the vault.
    
    Args:
        vault_addr: Address of the WeightedTreasuryVault
        
    Returns:
        List of weights in basis points (100 = 1%)
    """
    t = Treasury(vault_addr)
    return await t.get_weights()

@game_function(name="is_rebalance_needed")
async def is_rebalance_needed(
    vault_addr: str,
    new_weights: List[int],
    threshold_bps: int = 200
) -> bool:
    """
    Check if rebalance is needed based on weight difference.
    
    Args:
        vault_addr: Address of the WeightedTreasuryVault
        new_weights: New target weights (in basis points)
        threshold_bps: Threshold for rebalance in basis points (default 2%)
        
    Returns:
        True if rebalance is needed, False otherwise
    """
    t = Treasury(vault_addr)
    return await t.is_rebalance_needed(new_weights, threshold_bps)

@game_function(name="set_weights")
async def set_weights(
    vault_addr: str,
    signer_key: str,
    weights: List[int]
) -> str:
    """
    Set new target weights for the vault.
    
    Args:
        vault_addr: Address of the WeightedTreasuryVault
        signer_key: Private key for signing the transaction
        weights: New weights in basis points (must sum to 10000)
        
    Returns:
        Transaction hash
    """
    t = Treasury(vault_addr, signer_key)
    return await t.set_weights(weights)

@game_function(name="set_and_rebalance")
async def set_and_rebalance(
    vault_addr: str,
    signer_key: str,
    new_weights: List[int],           # basis‑points, len = assets
    sells: List[Dict[str, Any]],      # [{"token":addr,"amt":wei}, …]
    buys:  List[Dict[str, Any]],      # idem
    max_slippage_bps: int = DEFAULT_SLIPPAGE_BPS
) -> str:
    """
    Update weights and rebalance in two transactions.
    
    This function:
    1) Sets new target weights
    2) Executes a rebalance using Uniswap V3
    
    Args:
        vault_addr: Address of the WeightedTreasuryVault
        signer_key: Private key for signing transactions
        new_weights: New target weights in basis points (must sum to 10000)
        sells: List of assets to sell, each as {"token": address/symbol, "amt": wei_amount}
        buys: List of assets to buy, each as {"token": address/symbol, "amt": wei_amount}
        max_slippage_bps: Maximum allowed slippage in basis points (default: 30 = 0.3%)
        
    Returns:
        Transaction hash of the rebalance transaction
    """
    t = Treasury(vault_addr, signer_key)
    swap_data = build_swap_calldata(vault_addr, sells, buys, max_slippage_bps)
    return await t.set_and_rebalance(new_weights, swap_data)

@game_function(name="estimate_swap")
async def estimate_swap(
    sell_token: str,
    buy_token: str,
    sell_amount: int
) -> Dict[str, Any]:
    """
    Estimate the price and impact for a swap without executing it.
    
    Args:
        sell_token: Token to sell (symbol or address)
        buy_token: Token to buy (symbol or address)
        sell_amount: Amount of sell_token in wei
        
    Returns:
        Dictionary with price information including:
        - sell_token: Address of token being sold
        - buy_token: Address of token being bought
        - sell_amount: Amount being sold in wei
        - buy_amount: Estimated amount to receive in wei
        - price_impact: Estimated price impact as percentage
        - gas_estimate: Estimated gas cost
    """
    return estimate_swap_price(sell_token, buy_token, sell_amount)

@game_function(name="resolve_token_address")
def resolve_token_address(token_symbol_or_address: str) -> str:
    """
    Resolve a token symbol to its address.
    
    Args:
        token_symbol_or_address: Token symbol (e.g., 'ETH') or address
        
    Returns:
        Token address
        
    Supported symbols: ETH, WETH, USDCb, DAI, USDT
    """
    return resolve_token(token_symbol_or_address)
