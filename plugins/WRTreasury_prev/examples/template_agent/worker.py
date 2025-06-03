"""
Treasury Management Template Worker

This worker demonstrates how to manage a WeightedTreasuryVault using
the WhackRock Treasury plugin. It:

1. Gets weights from a strategy model
2. Checks if rebalancing is needed
3. Executes rebalances when the weights deviate by more than 2%
"""

import os
import logging
from game import Worker, game_function
from whackrock_treasury_plugin_gamesdk import (
    get_current_weights,
    set_and_rebalance,
    is_rebalance_needed,
    estimate_swap,
    resolve_token_address
)
from whackrock_treasury_plugin_gamesdk.config import (
    get_env, 
    DEFAULT_VAULT_ADDRESS,
    REBALANCE_THRESHOLD_BPS
)
from .signals import derive_weights

# Configure these values for your agent (will use environment variables if set)
VAULT_ADDRESS = get_env("TREASURY_VAULT_ADDRESS", "0xVAULT")  # Your vault address
SIGNER_KEY = get_env("TREASURY_SIGNER_KEY", "0x...")          # Private key for transactions
THRESHOLD_BPS = int(get_env("REBALANCE_THRESHOLD_BPS", "200"))  # Rebalance threshold (2%)

# Token addresses (you can use symbols like "ETH" or addresses)
TOKENS = {
    "stETH": "0xSTETH",   # Replace with actual addresses
    "WBTC": "0xWBTC",     # Or use resolve_token_address("WBTC")
    "USDT": "USDT"        # This will be resolved to the actual address
}

# Setup logging
logger = logging.getLogger("treasury_template")

class TemplateWorker(Worker):
    """
    Treasury Management Worker that rebalances the vault when 
    weights deviate from target.
    """
    
    def __init__(self, **kwargs):
        """Initialize the worker and check configuration"""
        super().__init__(**kwargs)
        
        # Log configuration (excluding private key)
        logger.info(f"Initialized with: Vault={VAULT_ADDRESS}, Threshold={THRESHOLD_BPS} bps")
        
        # Warn if using default values
        if VAULT_ADDRESS == "0xVAULT":
            logger.warning("Using placeholder vault address. Set TREASURY_VAULT_ADDRESS in .env")
        
        if SIGNER_KEY == "0x...":
            logger.warning("Using placeholder signer key. Set TREASURY_SIGNER_KEY in .env")
    
    async def calculate_swaps(self, current_weights, target_weights):
        """
        Calculate which assets to sell and buy based on weight differences
        
        This is a simplified approach - more sophisticated swap calculation
        would consider actual balances and prices
        """
        # Find assets to sell (over target) and buy (under target)
        sell_tokens = []
        buy_tokens = []
        
        # Create asset mapping between index and token address
        asset_map = list(TOKENS.items())
        
        for i, (token_name, addr) in enumerate(asset_map):
            # Convert from basis points to percentage
            curr_pct = current_weights[i] / 10000
            target_pct = target_weights[i] / 10000
            
            diff = curr_pct - target_pct
            if diff > 0.02:  # Over-allocated by more than 2%
                # Simplified approach - would calculate actual amounts in production
                sell_tokens.append({
                    "token": addr,
                    "amt": 100_000_000  # Example amount
                })
                logger.info(f"Need to sell {token_name}: current={curr_pct:.2%}, target={target_pct:.2%}")
            elif diff < -0.02:  # Under-allocated by more than 2%
                buy_tokens.append({
                    "token": addr,
                    "amt": 100_000_000  # Example amount
                })
                logger.info(f"Need to buy {token_name}: current={curr_pct:.2%}, target={target_pct:.2%}")
        
        # Simplified swap calculation
        # In a real implementation, you would calculate actual amounts
        # based on the asset prices and vault balances
        sells = sell_tokens[:1]  # Just take the first sell for this example
        buys = buy_tokens[:1]    # Just take the first buy for this example
        
        if sells and buys:
            # Estimate the swap to show pricing information
            try:
                logger.info(f"Estimating swap from {sells[0]['token']} to {buys[0]['token']}")
                estimate = await estimate_swap(
                    sells[0]["token"],
                    buys[0]["token"], 
                    sells[0]["amt"]
                )
                logger.info(f"Swap estimate: {estimate}")
                
                return sells, buys
            except Exception as e:
                logger.error(f"Failed to estimate swap: {e}")
                return [], []
        
        logger.info("No valid swap pairs identified")
        return [], []

    @game_function(schedule="*/30 * * * *")  # Run every 30 minutes
    async def manage(self):
        """
        Main treasury management function that:
        1. Gets current weights from the vault
        2. Gets target weights from the strategy
        3. Rebalances if needed
        """
        logger.info("Running treasury management cycle")
        
        try:
            # Get target weights from the strategy model
            # This returns percentages (0-1)
            target_percentages = await derive_weights()
            
            # Convert to basis points (0-10000)
            target_bps = [int(pct * 10000) for pct in target_percentages]
            
            # Get current weights from vault (already in basis points)
            logger.info(f"Getting current weights from vault: {VAULT_ADDRESS}")
            current_bps = await get_current_weights(VAULT_ADDRESS)
            
            logger.info(f"Current weights (bps): {current_bps}")
            logger.info(f"Target weights (bps): {target_bps}")
            
            # Check if rebalance is needed
            logger.info(f"Checking if rebalance needed (threshold: {THRESHOLD_BPS} bps)")
            needs_rebalance = await is_rebalance_needed(
                VAULT_ADDRESS, 
                target_bps, 
                THRESHOLD_BPS
            )
            
            if not needs_rebalance:
                logger.info("No rebalance needed, weights within threshold")
                return
                
            logger.info("Rebalance needed, calculating swaps")
            
            # Calculate what to sell and buy
            sells, buys = await self.calculate_swaps(current_bps, target_bps)
            
            if not sells or not buys:
                logger.info("No valid swaps to execute")
                return
            
            # Execute the rebalance
            try:
                logger.info("Executing rebalance transaction")
                tx_hash = await set_and_rebalance(
                    VAULT_ADDRESS, 
                    SIGNER_KEY, 
                    target_bps, 
                    sells, 
                    buys
                )
                logger.info(f"Rebalance executed. Transaction hash: {tx_hash}")
            except Exception as e:
                logger.error(f"Rebalance failed: {e}")
        except Exception as e:
            logger.error(f"Treasury management failed: {e}")
