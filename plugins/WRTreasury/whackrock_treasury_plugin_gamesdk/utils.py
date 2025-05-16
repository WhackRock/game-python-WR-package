"""
Utility functions for WhackRock Treasury management
"""

from typing import List, Dict, Any, Tuple
from decimal import Decimal
import logging

from .config import LOG_LEVEL

# Configure logging
logging_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=logging_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whackrock_treasury")

def validate_weights(weights: List[int], expected_sum: int = 10000) -> bool:
    """
    Validate that weights sum to the expected value
    
    Args:
        weights: List of weights to validate
        expected_sum: Expected sum of weights (default: 10000 basis points = 100%)
        
    Returns:
        True if valid, False otherwise
    """
    if not weights:
        return False
        
    actual_sum = sum(weights)
    if actual_sum != expected_sum:
        logger.warning(f"Invalid weights: sum is {actual_sum}, expected {expected_sum}")
        return False
    
    # Check for negative values
    if any(w < 0 for w in weights):
        logger.warning("Invalid weights: negative values are not allowed")
        return False
        
    return True

def calculate_deviation(current: List[int], target: List[int]) -> List[int]:
    """
    Calculate the deviation between current and target weights
    
    Args:
        current: Current weights in basis points
        target: Target weights in basis points
        
    Returns:
        List of deviations in basis points
    """
    if len(current) != len(target):
        raise ValueError(f"Length mismatch: current ({len(current)}) vs target ({len(target)})")
        
    return [c - t for c, t in zip(current, target)]

def format_basis_points(bps: int) -> str:
    """
    Format basis points as a human-readable percentage
    
    Args:
        bps: Value in basis points
        
    Returns:
        Formatted string (e.g., "12.34%")
    """
    return f"{bps / 100:.2f}%"

def format_token_amount(amount: int, decimals: int = 18) -> str:
    """
    Format token amount for display
    
    Args:
        amount: Amount in wei/smallest unit
        decimals: Token decimals
        
    Returns:
        Formatted string
    """
    value = Decimal(amount) / Decimal(10 ** decimals)
    
    if value < 0.00001:
        return f"{value:.8f}"
    elif value < 0.001:
        return f"{value:.6f}"
    elif value < 1:
        return f"{value:.4f}"
    elif value < 1000:
        return f"{value:.2f}"
    elif value < 1000000:
        return f"{value/1000:.2f}K"
    else:
        return f"{value/1000000:.2f}M"

def weighted_allocate(total_value: Decimal, weights: List[int]) -> List[Decimal]:
    """
    Calculate the value allocation based on weights
    
    Args:
        total_value: Total value to allocate
        weights: List of weights in basis points
        
    Returns:
        List of allocated values
    """
    if not validate_weights(weights):
        raise ValueError("Invalid weights")
        
    return [total_value * Decimal(w) / Decimal(10000) for w in weights]

def calculate_rebalance_amounts(
    current_values: List[Decimal], 
    target_weights: List[int],
    threshold_bps: int = 200
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Calculate amounts to sell and buy to reach target weights
    
    Args:
        current_values: Current values for each asset
        target_weights: Target weights in basis points
        threshold_bps: Threshold for rebalance in basis points
        
    Returns:
        Tuple of (sells, buys) lists
    """
    total_value = sum(current_values)
    target_values = weighted_allocate(total_value, target_weights)
    
    sells = []
    buys = []
    
    for i, (current, target) in enumerate(zip(current_values, target_values)):
        if current == 0 and target == 0:
            continue
            
        current_weight = int((current / total_value) * 10000) if total_value > 0 else 0
        target_weight = target_weights[i]
        
        # If deviation is greater than threshold
        if abs(current_weight - target_weight) > threshold_bps:
            diff = current - target
            
            if diff > 0:  # Need to sell
                sells.append({
                    "index": i,
                    "amount": diff,
                    "current_weight": current_weight,
                    "target_weight": target_weight,
                    "deviation": current_weight - target_weight
                })
            elif diff < 0:  # Need to buy
                buys.append({
                    "index": i,
                    "amount": abs(diff),
                    "current_weight": current_weight,
                    "target_weight": target_weight,
                    "deviation": target_weight - current_weight
                })
    
    # Sort by deviation (largest first)
    sells.sort(key=lambda x: x["deviation"], reverse=True)
    buys.sort(key=lambda x: x["deviation"], reverse=True)
    
    return sells, buys 