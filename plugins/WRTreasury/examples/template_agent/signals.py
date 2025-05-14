"""
Very simple starter strategy:

* Reads Uniswap TWAP prices from the global oracle.
* Allocates:
    • 70 % to the **best‑performing** of stETH or WBTC in the last 30 min
    • 30 % remains in USDT (stable buffer)

Edit this file only; leave worker/core libs intact.
"""

import os, asyncio
from web3 import AsyncWeb3
from decimal import Decimal
ORACLE = "0xORACLE"         # same address used by vaults
W3     = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(os.environ["BASE_RPC"]))

TOKENS = {
    "stETH": "0xSTETH",
    "WBTC":  "0xWBTC",
    "USDT":  "0xUSDT"
}

ORACLE_ABI = [
    {"inputs":[{"internalType":"address","name":"token","type":"address"}],
     "name":"usdPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"}
]

oracle = W3.eth.contract(address=ORACLE, abi=ORACLE_ABI)

async def price(token):
    return await oracle.functions.usdPrice(token).call()

async def derive_weights() -> list[float]:
    st = Decimal(await price(TOKENS["stETH"]))
    wb = Decimal(await price(TOKENS["WBTC"]))

    if st > wb:
        return [0.70, 0.00, 0.30]     # stETH winner
    else:
        return [0.00, 0.70, 0.30]     # WBTC winner

if __name__ == "__main__":
    print(asyncio.run(derive_weights()))
