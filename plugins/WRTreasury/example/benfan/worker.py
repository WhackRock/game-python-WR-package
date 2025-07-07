"""
Minimal WhackRock Fund rebalancing worker using GAME SDK.

This worker demonstrates how to use the WhackRockFundManagerSDK to automatically
rebalance a fund based on signals. It uses set_target_weights with rebalance_if_needed=True
to update allocations and trigger rebalancing in a single transaction.
"""

import os
from typing import Tuple
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus

# Import our signal generator and fund manager SDK
from .signal import get_target_weights_bps, get_signal_description
from ..whackrock_plugin_gamesdk.whackrock_fund_manager_gamesdk import WhackRockFundManagerSDK

# Configuration - Replace with your actual values
WEB3_PROVIDER = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"  # Replace with your RPC endpoint
FUND_CONTRACT_ADDRESS = "0x..."  # Replace with actual fund contract address
AGENT_PRIVATE_KEY = "0x..."  # Replace with agent's private key (keep secure!)
AGENT_ADDRESS = "0x..."  # Replace with agent's address

def create_rebalance_worker():
    """Create a GAME SDK worker that rebalances a WhackRock fund based on signals"""
    
    # Initialize the fund manager SDK
    fund_sdk = WhackRockFundManagerSDK(
        web3_provider=WEB3_PROVIDER,
        fund_contract_address=FUND_CONTRACT_ADDRESS,
        private_key=AGENT_PRIVATE_KEY,
        account_address=AGENT_ADDRESS
    )
    
    def rebalance_fund(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """
        Rebalance the fund based on the current signal.
        This is the only function this worker performs.
        """
        try:
            # Get the current signal
            target_weights_bps = get_target_weights_bps()
            signal_description = get_signal_description()
            
            # Convert to comma-separated string format expected by the SDK
            weights_str = ",".join(map(str, target_weights_bps))
            
            # Set target weights and rebalance in one transaction
            result = fund_sdk.set_target_weights(
                weights_bps=target_weights_bps,
                rebalance_if_needed=True,  # This triggers automatic rebalancing
                gas_limit=800000  # Higher gas limit for rebalancing transaction
            )
            
            if not result['success']:
                return FunctionResultStatus.FAILED, f"Rebalancing failed: {result['error']}", result
            
            # Success message
            message = f"Fund rebalanced successfully!\n"
            message += f"Signal: {signal_description}\n"
            message += f"New weights (BPS): {target_weights_bps}\n"
            message += f"Transaction hash: {result['tx_hash']}\n"
            message += f"Gas used: {result['gas_used']}"
            
            return FunctionResultStatus.DONE, message, result
            
        except Exception as e:
            return FunctionResultStatus.FAILED, f"Rebalancing error: {str(e)}", {}
    
    # Define the single action this worker can perform
    action_space = [
        Function(
            fn_name="rebalance_fund",
            fn_description="Rebalance the fund based on current signal and trigger immediate rebalancing",
            args=[],
            executable=rebalance_fund
        )
    ]
    
    # State management function
    def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
        """Track rebalancing state"""
        if current_state is None:
            current_state = {
                "last_rebalance": None,
                "rebalance_count": 0,
                "last_weights": None,
                "last_signal": None
            }
        
        if function_result and function_result.fn_name == "rebalance_fund":
            info = function_result.info
            current_state["last_rebalance"] = info.get("tx_hash")
            current_state["rebalance_count"] += 1
            current_state["last_weights"] = info.get("weights_set")
            current_state["last_signal"] = get_signal_description()
        
        return current_state
    
    # Create the worker
    game_api_key = os.environ.get("GAME_API_KEY")
    if not game_api_key:
        raise ValueError("GAME_API_KEY environment variable is required")
    
    worker = Worker(
        api_key=game_api_key,
        description="WhackRock Fund Rebalancer - Automatically rebalances fund based on signals",
        instruction="""
        You are a fund rebalancing agent. Your single responsibility is to rebalance 
        the WhackRock fund based on the current signal.
        
        When asked to rebalance or when you detect it's time for rebalancing:
        1. Call the rebalance_fund function
        2. This will get the current signal, set new target weights, and trigger rebalancing
        3. Report the results including transaction hash and gas used
        
        You should rebalance immediately when requested.
        """,
        get_state_fn=get_state_fn,
        action_space=action_space,
        model_name="Llama-3.1-405B-Instruct"
    )
    
    return worker

def run_rebalance_worker():
    """Run the rebalancing worker"""
    print("Starting WhackRock Fund Rebalancing Worker...")
    
    try:
        worker = create_rebalance_worker()
        
        # Run the worker with instruction to rebalance
        result = worker.run("Please rebalance the fund based on the current signal")
        print(f"Worker execution completed: {result}")
        
    except Exception as e:
        print(f"Error running rebalance worker: {e}")

if __name__ == "__main__":
    # Test the signal first
    weights = get_target_weights_bps()
    description = get_signal_description()
    print(f"Current signal: {description}")
    print(f"Target weights: {weights}")
    
    # Uncomment to run the actual worker (requires proper configuration)
    # run_rebalance_worker()