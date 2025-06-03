from game import Worker, game_function
from whackrock_treasury_plugin_gamesdk import (
    get_current_weights, set_and_rebalance
)
from .signals import derive_weights

VAULT  = "0xBENFANVAULT"
SIGNER = "0x..."

class BenFanWorker(Worker):
    @game_function(schedule="0 */1 * * *")   # hourly
    async def manage(self):
        target = await derive_weights()
        curr   = await get_current_weights(VAULT)
        if max(abs(ci/1e4 - ti) for ci, ti in zip(curr, target)) < 0.02:
            return
        # build simple sell/buy lists (omitted)
        sells, buys = plan_deltas(curr, target)
        await set_and_rebalance(VAULT, SIGNER, [int(t*1e4) for t in target], sells, buys)
