"""
Example usage of the WhackRock Fund Manager GAME SDK

This example demonstrates how to:
1. Initialize the SDK
2. Get current and target weights
3. Check if rebalancing is needed
4. Trigger a rebalance (if you're the agent)
5. Integrate with GAME SDK for autonomous agents
"""

from whackrock_fund_manager_gamesdk import WhackRockFundManagerSDK, create_fund_manager_functions
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import FunctionResult
import os


def example_basic_usage():
    """Basic usage example of the WhackRock Fund Manager SDK"""
    
    # Initialize the SDK
    web3_provider = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"  # Replace with your provider
    fund_address = "0x..."  # Replace with actual fund contract address
    
    # For read-only operations
    sdk = WhackRockFundManagerSDK(
        web3_provider=web3_provider,
        fund_contract_address=fund_address
    )
    
    # Get fund information
    print("=== Fund Information ===")
    fund_info = sdk.get_fund_info()
    if 'error' not in fund_info:
        print(f"Fund Address: {fund_info['fund_address']}")
        print(f"Agent Address: {fund_info['agent_address']}")
        print(f"Total NAV (WETH): {fund_info['total_nav_weth_formatted']:.4f} WETH")
        print(f"Total NAV (USDC): ${fund_info['total_nav_usdc_formatted']:,.2f}")
    else:
        print(f"Error: {fund_info['error']}")
    
    # Get current weights
    print("\n=== Current Weights ===")
    current = sdk.get_current_weights()
    if 'error' not in current:
        for token in current['tokens_with_weights']:
            print(f"{token['token_address']}: {token['weight_percent']:.2f}%")
    else:
        print(f"Error: {current['error']}")
    
    # Get target weights
    print("\n=== Target Weights ===")
    target = sdk.get_target_weights()
    if 'error' not in target:
        for token in target['tokens_with_weights']:
            print(f"{token['token_address']}: {token['weight_percent']:.2f}%")
    else:
        print(f"Error: {target['error']}")
    
    # Compare weights
    print("\n=== Weight Comparison ===")
    comparison = sdk.compare_weights()
    if 'error' not in comparison:
        print(f"Needs Rebalance: {comparison['needs_rebalance']}")
        print(f"Max Deviation: {comparison['max_deviation_percent']:.2f}%")
        for comp in comparison['comparisons']:
            if comp['deviation_percent'] > 0.1:
                print(f"{comp['token_address']}: {comp['deviation_percent']:.2f}% deviation")
    else:
        print(f"Error: {comparison['error']}")


def example_with_write_operations():
    """Example with write operations (triggering rebalance)"""
    
    # Initialize SDK with private key for write operations
    web3_provider = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"
    fund_address = "0x..."  # Replace with actual fund contract address
    private_key = "0x..."  # Replace with agent's private key (keep secure!)
    account_address = "0x..."  # Replace with agent's address
    
    sdk = WhackRockFundManagerSDK(
        web3_provider=web3_provider,
        fund_contract_address=fund_address,
        private_key=private_key,
        account_address=account_address
    )
    
    # Check if rebalance is needed
    comparison = sdk.compare_weights()
    if 'error' not in comparison and comparison['needs_rebalance']:
        print("Rebalance needed, triggering...")
        result = sdk.trigger_rebalance()
        if result['success']:
            print(f"Rebalance successful! TX: {result['tx_hash']}")
        else:
            print(f"Rebalance failed: {result['error']}")
    else:
        print("No rebalance needed")


def example_game_sdk_integration():
    """Example of integrating with GAME SDK for autonomous agents"""
    
    # Initialize the WhackRock SDK
    web3_provider = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"
    fund_address = "0x..."
    
    sdk = WhackRockFundManagerSDK(
        web3_provider=web3_provider,
        fund_contract_address=fund_address
    )
    
    # Create GAME SDK functions
    fund_functions = create_fund_manager_functions(sdk)
    
    # Define state management function
    def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
        """Update state based on function results"""
        if current_state is None:
            current_state = {
                "last_check": None,
                "needs_rebalance": False,
                "current_weights": {},
                "target_weights": {},
                "max_deviation": 0
            }
        
        # Update state based on the function that was called
        if function_result.fn_name == "check_rebalance_needed":
            info = function_result.info
            current_state["needs_rebalance"] = info.get("needs_rebalance", False)
            current_state["max_deviation"] = info.get("max_deviation_percent", 0)
            current_state["last_check"] = "rebalance_check"
        
        elif function_result.fn_name == "get_current_weights":
            info = function_result.info
            current_state["current_weights"] = {
                token["token_address"]: token["weight_percent"] 
                for token in info.get("tokens_with_weights", [])
            }
        
        elif function_result.fn_name == "get_target_weights":
            info = function_result.info
            current_state["target_weights"] = {
                token["token_address"]: token["weight_percent"] 
                for token in info.get("tokens_with_weights", [])
            }
        
        return current_state
    
    # Create a GAME SDK Worker
    game_api_key = os.environ.get("GAME_API_KEY")
    
    worker = Worker(
        api_key=game_api_key,
        description="WhackRock Fund Manager - monitors and rebalances fund portfolios",
        instruction="""
        You are a fund management agent for WhackRock funds. Your responsibilities are:
        1. Monitor the current asset weights vs target weights
        2. Check if rebalancing is needed (deviation > 1%)
        3. Alert when rebalancing is required
        4. Provide fund status updates when requested
        
        Start by getting the fund information and checking if rebalancing is needed.
        """,
        get_state_fn=get_state_fn,
        action_space=fund_functions,
        model_name="Llama-3.1-405B-Instruct"
    )
    
    # Run the worker
    print("Starting WhackRock Fund Manager Agent...")
    worker.run("Check the fund status and determine if rebalancing is needed")


if __name__ == "__main__":
    # Run basic example
    print("=== BASIC USAGE EXAMPLE ===\n")
    example_basic_usage()
    
    # Uncomment to run write operations example (requires agent private key)
    # print("\n\n=== WRITE OPERATIONS EXAMPLE ===\n")
    # example_with_write_operations()
    
    # Uncomment to run GAME SDK integration example (requires GAME_API_KEY)
    # print("\n\n=== GAME SDK INTEGRATION EXAMPLE ===\n")
    # example_game_sdk_integration()