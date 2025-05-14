from game import Worker, game_function
from whackrock_treasury_plugin_gamesdk import (
    get_current_weights,
    set_and_rebalance,
)
from .signals import derive_weights

VAULT = "0xVAULT"
SIGNER = "0x..."

class TemplateWorker(Worker):
    @game_function(schedule="*/30 * * * *")
    async def manage(self):
        target = derive_weights()
        curr   = await get_current_weights(VAULT)
        if max(abs(ci/1e4 - ti) for ci, ti in zip(curr, target)) < 0.02:
            return
        # naive sell/buy plan (left as exercise)
        sells = [...]
        buys  = [...]
        await set_and_rebalance(VAULT, SIGNER, [int(t*1e4) for t in target], sells, buys)
