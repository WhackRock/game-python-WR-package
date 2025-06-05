import json
import os
from typing import List, Tuple, cast

from game.action import Action
from game.plugin import Plugin
from game.types import Address, BigNumber
from game.beaucop_dargs import BeaucoupDArgs, Arg

# --- Load ABI from JSON file ---
plugin_dir = os.path.dirname(os.path.abspath(__file__))
abi_file_path = os.path.join(plugin_dir, "IWhackRockFund.json")

IWHACKROCKFUND_ABI_LIST = []
try:
    with open(abi_file_path, 'r') as f:
        abi_data = json.load(f)
        if "abi" in abi_data and isinstance(abi_data["abi"], list):
            IWHACKROCKFUND_ABI_LIST = abi_data["abi"]
        else:
            # Fallback or error if the JSON doesn't have the expected "abi" key with a list
            print(f"ERROR: ABI file '{abi_file_path}' is not in the expected format (missing 'abi' key or not a list).")
except FileNotFoundError:
    print(f"ERROR: ABI file '{abi_file_path}' not found.")
except json.JSONDecodeError:
    print(f"ERROR: Could not decode JSON from ABI file '{abi_file_path}'.")
    # Proceed with an empty list.

IWHACKROCKFUND_ABI_STR = json.dumps(IWHACKROCKFUND_ABI_LIST)

if not IWHACKROCKFUND_ABI_LIST: # If loading failed, IWHACKROCKFUND_ABI_STR would be '[]'
    print("WARNING: WhackRockFundPlugin is using an empty ABI due to loading errors. Actions will likely fail.")


# --- Action Classes ---
class GetCurrentCompositionAction(Action):
    name = "whackrock_get_current_composition"
    description = "Get the current asset composition (weights BPS, addresses, symbols) of an IWhackRockFund."
    abi = IWHACKROCKFUND_ABI_STR # Use the loaded ABI string

    class Arguments(BeaucoupDArgs):
        fund_address: Address = Arg(help="The address of the IWhackRockFund contract.")

    def execute(self) -> Tuple[List[BigNumber], List[Address], List[str]]:
        if not IWHACKROCKFUND_ABI_LIST: # Check if ABI loading failed
            raise RuntimeError("IWhackRockFund ABI not loaded. Cannot execute action.")
            
        fund_contract = self.virtual.contract_from_address_and_abi(
            self.args.fund_address, self.abi
        )
        composition_bps_raw, addresses_raw, symbols_raw = fund_contract.functions.getCurrentCompositionBPS().call()
        
        processed_composition_bps = [BigNumber(w) for w in composition_bps_raw]
        return processed_composition_bps, addresses_raw, symbols_raw

class GetTargetCompositionAction(Action):
    name = "whackrock_get_target_composition"
    description = "Get the target asset composition (weights BPS, addresses, symbols) of an IWhackRockFund."
    abi = IWHACKROCKFUND_ABI_STR # Use the loaded ABI string

    class Arguments(BeaucoupDArgs):
        fund_address: Address = Arg(help="The address of the IWhackRockFund contract.")

    def execute(self) -> Tuple[List[BigNumber], List[Address], List[str]]:
        if not IWHACKROCKFUND_ABI_LIST:
            raise RuntimeError("IWhackRockFund ABI not loaded. Cannot execute action.")

        fund_contract = self.virtual.contract_from_address_and_abi(
            self.args.fund_address, self.abi
        )
        composition_bps_raw, addresses_raw, symbols_raw = fund_contract.functions.getTargetCompositionBPS().call()
        processed_composition_bps = [BigNumber(w) for w in composition_bps_raw]
        return processed_composition_bps, addresses_raw, symbols_raw

class SetTargetWeightsAction(Action):
    name = "whackrock_set_target_weights"
    description = "Set the target weights for assets in an IWhackRockFund."
    abi = IWHACKROCKFUND_ABI_STR # Use the loaded ABI string

    class Arguments(BeaucoupDArgs):
        fund_address: Address = Arg(help="The address of the IWhackRockFund contract.")
        weights_bps: List[BigNumber] = Arg(help="List of target weights in basis points (e.g., [5000, 5000]).")

    def execute(self) -> str:
        if not IWHACKROCKFUND_ABI_LIST:
            raise RuntimeError("IWhackRockFund ABI not loaded. Cannot execute action.")

        fund_contract = self.virtual.contract_from_address_and_abi(
            self.args.fund_address, self.abi
        )
        raw_weights_bps = [int(w.value) for w in self.args.weights_bps]
        
        txn_receipt = self.blockchain_interface.transact_sync(
            fund_contract.functions.setTargetWeights(raw_weights_bps)
        )
        return f"Target weights set for fund {self.args.fund_address}. Txn: {txn_receipt.transactionHash.hex()}"

class TriggerRebalanceAction(Action):
    name = "whackrock_trigger_rebalance"
    description = "Manually trigger a rebalance for an IWhackRockFund."
    abi = IWHACKROCKFUND_ABI_STR # Use the loaded ABI string

    class Arguments(BeaucoupDArgs):
        fund_address: Address = Arg(help="The address of the IWhackRockFund contract.")

    def execute(self) -> str:
        if not IWHACKROCKFUND_ABI_LIST:
            raise RuntimeError("IWhackRockFund ABI not loaded. Cannot execute action.")

        fund_contract = self.virtual.contract_from_address_and_abi(
            self.args.fund_address, self.abi
        )
        txn_receipt = self.blockchain_interface.transact_sync(
            fund_contract.functions.triggerRebalance()
        )
        return f"Rebalance triggered for fund {self.args.fund_address}. Txn: {txn_receipt.transactionHash.hex()}"

class SetTargetWeightsAndRebalanceAction(Action):
    name = "whackrock_set_weights_and_rebalance"
    description = "Set target weights and then trigger a rebalance if needed for an IWhackRockFund."
    abi = IWHACKROCKFUND_ABI_STR # Use the loaded ABI string

    class Arguments(BeaucoupDArgs):
        fund_address: Address = Arg(help="The address of the IWhackRockFund contract.")
        weights_bps: List[BigNumber] = Arg(help="List of target weights in basis points.")

    def execute(self) -> str:
        if not IWHACKROCKFUND_ABI_LIST:
            raise RuntimeError("IWhackRockFund ABI not loaded. Cannot execute action.")
            
        fund_contract = self.virtual.contract_from_address_and_abi(
            self.args.fund_address, self.abi
        )
        raw_weights_bps = [int(w.value) for w in self.args.weights_bps]
        txn_receipt = self.blockchain_interface.transact_sync(
            fund_contract.functions.setTargetWeightsAndRebalanceIfNeeded(raw_weights_bps)
        )
        return f"Set target weights and potentially rebalanced fund {self.args.fund_address}. Txn: {txn_receipt.transactionHash.hex()}"

# --- Plugin Class ---
class WhackRockFundPlugin(Plugin):
    name = "whackrock_fund_manager"
    description = "A plugin to interact with IWhackRockFund compatible funds for rebalancing and weight management."
    actions = [
        GetCurrentCompositionAction,
        GetTargetCompositionAction,
        SetTargetWeightsAction,
        TriggerRebalanceAction,
        SetTargetWeightsAndRebalanceAction,
    ]
    def_plugin_admin_actions = []
    web_views = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not IWHACKROCKFUND_ABI_LIST:
            print(f"CRITICAL WARNING: WhackRockFundPlugin ({self.name}) loaded with an empty ABI. "
                  f"This usually means 'IWhackRockFund.json' was not found or was invalid.")

