"""
WhackRock Treasury Game‑SDK functions
"""

from game import game_function
from .treasury import Treasury
from .uniswap  import build_swap_calldata

@game_function(name="get_current_weights")
async def get_current_weights(vault_addr: str) -> list[int]:
    """Return the on‑chain targetWeights() array."""
    t = Treasury(vault_addr)
    return await t.get_weights()

@game_function(name="set_and_rebalance")
async def set_and_rebalance(
    vault_addr: str,
    signer_key: str,
    new_weights: list[int],           # basis‑points, len = assets
    sells: list[dict],                # [{"token":addr,"amt":wei}, …]
    buys:  list[dict],                # idem
) -> str:
    """
    1) setWeights(new)
    2) rebalance(swaps) with Universal Router calldata
    Returns tx hash of the rebalance.
    """
    t = Treasury(vault_addr, signer_key)
    swap_data = build_swap_calldata(vault_addr, sells, buys)
    return await t.set_and_rebalance(new_weights, swap_data)
