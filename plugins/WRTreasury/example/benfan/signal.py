"""
Minimal signal generator for WhackRock Fund rebalancing example.

Returns target weights in basis points for the fund's allowed tokens.
For demo purposes, this uses a simple rotating signal between different allocations.
"""

import time
from typing import List

# Number of tokens in the fund (must match fund's allowedTokens length)
NUM_FUND_ASSETS = 3

def get_target_weights_bps() -> List[int]:
    """
    Generate target weights in basis points (BPS) for fund rebalancing.
    
    Returns:
        List of weights in BPS that sum to 10000 (100%)
    
    For demo purposes, this rotates between different allocation strategies
    based on current time to show rebalancing in action.
    """
    
    # Get current minute to create a simple rotating signal
    current_minute = int(time.time() / 60) % 4
    
    if current_minute == 0:
        # Conservative allocation: 50%, 30%, 20%
        return [5000, 3000, 2000]
    elif current_minute == 1:
        # Balanced allocation: 40%, 40%, 20%
        return [4000, 4000, 2000]
    elif current_minute == 2:
        # Aggressive allocation: 60%, 25%, 15%
        return [6000, 2500, 1500]
    else:
        # Equal weight allocation: 33.33%, 33.33%, 33.34%
        return [3333, 3333, 3334]

def get_signal_description() -> str:
    """
    Get a description of the current signal.
    
    Returns:
        Human-readable description of the current allocation strategy
    """
    weights = get_target_weights_bps()
    percentages = [w / 100 for w in weights]
    
    current_minute = int(time.time() / 60) % 4
    strategies = [
        "Conservative",
        "Balanced", 
        "Aggressive",
        "Equal Weight"
    ]
    
    strategy = strategies[current_minute]
    weight_str = ", ".join([f"{p:.1f}%" for p in percentages])
    
    return f"{strategy} allocation: {weight_str}"

# Simple test
if __name__ == "__main__":
    weights = get_target_weights_bps()
    description = get_signal_description()
    print(f"Current signal: {description}")
    print(f"Weights (BPS): {weights}")
    print(f"Total: {sum(weights)} BPS")