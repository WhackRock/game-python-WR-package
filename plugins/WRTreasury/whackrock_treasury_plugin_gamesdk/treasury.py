from web3 import AsyncWeb3
from .config import w3, VAULT_ABI   # import your compiled ABI JSON

class Treasury:
    def __init__(self, address: str, signer_key: str | None = None):
        self.vault = w3.eth.contract(address=address, abi=VAULT_ABI)
        self.signer = (
            w3.eth.account.from_key(signer_key) if signer_key else None
        )

    async def get_weights(self) -> list[int]:
        return await self.vault.functions.targetWeights().call()

    async def set_and_rebalance(self, weights, swap_data):
        if not self.signer:
            raise ValueError("signer_key required")

        tx1 = self.vault.functions.setWeights(weights).build_transaction(
            {"from": self.signer.address}
        )
        tx2 = self.vault.functions.rebalance(swap_data).build_transaction(
            {"from": self.signer.address, "gas": 2_400_000}
        )

        for raw in (tx1, tx2):
            signed = self.signer.sign_transaction(raw)
            await w3.eth.send_raw_transaction(signed.rawTransaction)
        return signed.hash.hex()
