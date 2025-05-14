import requests, time

UNIVERSAL_ROUTER = "0x3fC91a3AFd70395cD496c647D5A6cC9D4b2B7Fad"  # Base
CHAIN_ID = 8453

def build_swap_calldata(vault_addr, sells, buys, max_slip_bps=30):
    """
    Bundles *one* exact‑in swap for simplicity.
    sells / buys = [{"token":addr, "amt":wei}]
    """
    src = sells[0]; dst = buys[0]
    q = (
        f"tokenIn={src['token']}&tokenOut={dst['token']}"
        f"&amount={src['amt']}&type=exactIn"
        f"&chainId={CHAIN_ID}&slippageToleranceBps={max_slip_bps}"
    )
    quote = requests.get(f"https://router.uniswap.org/quote?{q}").json()
    return quote["methodParameters"]["calldata"]
