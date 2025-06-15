"""
WhackRock Treasury Plugin for GAME SDK

This plugin provides functions for AI agents to interact with WhackRockFund smart contracts,
enabling portfolio management, rebalancing, and fee collection operations.
"""

import json
import os
from typing import List, Dict, Any, Optional
from web3 import Web3
from web3.contract import Contract
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus

# Load ABI
abi_path = os.path.join(os.path.dirname(__file__), "IWhackRockFund.json")
with open(abi_path, "r") as f:
    WHACKROCK_FUND_ABI = json.load(f)["abi"]


class WhackRockPlugin:
    """
    WhackRock Treasury Plugin for managing investment funds via AI agents.
    
    This plugin enables AI agents to:
    - Set portfolio target weights
    - Trigger rebalancing operations
    - Monitor fund performance
    - Collect management fees
    - Query fund composition and NAV
    """
    
    def __init__(self, rpc_url: str, fund_address: str, private_key: Optional[str] = None):
        """
        Initialize the WhackRock plugin.
        
        Args:
            rpc_url: Ethereum RPC URL (e.g., Base mainnet)
            fund_address: Address of the WhackRockFund contract
            private_key: Private key for signing transactions (optional for read-only)
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.fund_address = Web3.to_checksum_address(fund_address)
        self.contract: Contract = self.w3.eth.contract(
            address=self.fund_address,
            abi=WHACKROCK_FUND_ABI
        )
        
        if private_key:
            self.account = self.w3.eth.account.from_key(private_key)
            self.w3.eth.default_account = self.account.address
        else:
            self.account = None
    
    def _execute_transaction(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Execute a transaction and return the result."""
        if not self.account:
            raise Exception("Private key required for write operations")
        
        # Build transaction
        tx = func(*args, **kwargs).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': kwargs.get('gas', 500000),
            'gasPrice': self.w3.eth.gas_price,
        })
        
        # Sign and send
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'transactionHash': receipt['transactionHash'].hex(),
            'status': receipt['status'],
            'gasUsed': receipt['gasUsed'],
            'blockNumber': receipt['blockNumber']
        }
    
    # Read Functions
    
    def get_current_composition(self) -> Dict[str, Any]:
        """Get the current portfolio composition in basis points."""
        try:
            result = self.contract.functions.getCurrentCompositionBPS().call()
            weights, addresses, symbols = result
            
            composition = []
            for i in range(len(addresses)):
                composition.append({
                    'address': addresses[i],
                    'symbol': symbols[i],
                    'weight_bps': weights[i],
                    'weight_percent': weights[i] / 100
                })
            
            return {
                'status': 'success',
                'composition': composition
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_target_composition(self) -> Dict[str, Any]:
        """Get the target portfolio composition in basis points."""
        try:
            result = self.contract.functions.getTargetCompositionBPS().call()
            weights, addresses, symbols = result
            
            composition = []
            for i in range(len(addresses)):
                composition.append({
                    'address': addresses[i],
                    'symbol': symbols[i],
                    'weight_bps': weights[i],
                    'weight_percent': weights[i] / 100
                })
            
            return {
                'status': 'success',
                'composition': composition
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_total_nav_weth(self) -> Dict[str, Any]:
        """Get total NAV in WETH (accounting asset)."""
        try:
            nav = self.contract.functions.totalNAVInAccountingAsset().call()
            nav_eth = self.w3.from_wei(nav, 'ether')
            
            return {
                'status': 'success',
                'nav_wei': nav,
                'nav_eth': float(nav_eth)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_total_nav_usdc(self) -> Dict[str, Any]:
        """Get total NAV in USDC."""
        try:
            nav = self.contract.functions.totalNAVInUSDC().call()
            # USDC has 6 decimals
            nav_usdc = nav / 10**6
            
            return {
                'status': 'success',
                'nav_raw': nav,
                'nav_usdc': float(nav_usdc)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get current agent address and fee information."""
        try:
            agent = self.contract.functions.agent().call()
            fee_bps = self.contract.functions.agentAumFeeBps().call()
            fee_wallet = self.contract.functions.agentAumFeeWallet().call()
            last_collection = self.contract.functions.lastAgentAumFeeCollectionTimestamp().call()
            
            return {
                'status': 'success',
                'agent_address': agent,
                'fee_bps': fee_bps,
                'fee_percent': fee_bps / 100,
                'fee_wallet': fee_wallet,
                'last_fee_collection_timestamp': last_collection
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    # Write Functions
    
    def set_target_weights(self, weights: List[int]) -> Dict[str, Any]:
        """
        Set target portfolio weights.
        
        Args:
            weights: List of weights in basis points (must sum to 10000)
        """
        try:
            # Validate weights
            if sum(weights) != 10000:
                return {
                    'status': 'error',
                    'error': f'Weights must sum to 10000 bps, got {sum(weights)}'
                }
            
            result = self._execute_transaction(
                self.contract.functions.setTargetWeights,
                weights
            )
            
            return {
                'status': 'success',
                'transaction': result
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def set_weights_and_rebalance(self, weights: List[int]) -> Dict[str, Any]:
        """
        Set target weights and trigger rebalance if needed.
        
        Args:
            weights: List of weights in basis points (must sum to 10000)
        """
        try:
            # Validate weights
            if sum(weights) != 10000:
                return {
                    'status': 'error',
                    'error': f'Weights must sum to 10000 bps, got {sum(weights)}'
                }
            
            result = self._execute_transaction(
                self.contract.functions.setTargetWeightsAndRebalanceIfNeeded,
                weights,
                gas=1000000  # Higher gas limit for rebalancing
            )
            
            return {
                'status': 'success',
                'transaction': result
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def trigger_rebalance(self) -> Dict[str, Any]:
        """Trigger portfolio rebalancing."""
        try:
            result = self._execute_transaction(
                self.contract.functions.triggerRebalance,
                gas=1000000
            )
            
            return {
                'status': 'success',
                'transaction': result
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def collect_management_fee(self) -> Dict[str, Any]:
        """Collect accrued management fees."""
        try:
            result = self._execute_transaction(
                self.contract.functions.collectAgentManagementFee
            )
            
            return {
                'status': 'success',
                'transaction': result
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    # Helper Functions
    
    def calculate_rebalance_needed(self) -> Dict[str, Any]:
        """Check if rebalancing is needed based on deviation threshold."""
        try:
            current = self.get_current_composition()
            target = self.get_target_composition()
            
            if current['status'] != 'success' or target['status'] != 'success':
                return {
                    'status': 'error',
                    'error': 'Failed to get compositions'
                }
            
            # Calculate maximum deviation
            max_deviation = 0
            deviations = []
            
            for i in range(len(current['composition'])):
                curr_weight = current['composition'][i]['weight_bps']
                targ_weight = target['composition'][i]['weight_bps']
                
                if targ_weight > 0:
                    deviation = abs(curr_weight - targ_weight)
                    deviation_percent = (deviation / targ_weight) * 100
                    
                    deviations.append({
                        'symbol': current['composition'][i]['symbol'],
                        'current_bps': curr_weight,
                        'target_bps': targ_weight,
                        'deviation_percent': deviation_percent
                    })
                    
                    max_deviation = max(max_deviation, deviation_percent)
            
            # Threshold is 1% (100 bps)
            needs_rebalance = max_deviation > 1.0
            
            return {
                'status': 'success',
                'needs_rebalance': needs_rebalance,
                'max_deviation_percent': max_deviation,
                'deviations': deviations
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


def get_whackrock_functions(rpc_url: str, fund_address: str, private_key: Optional[str] = None) -> List[Function]:
    """
    Get GAME SDK functions for WhackRock fund management.
    
    Returns a list of Function objects that can be used by GAME agents.
    """
    plugin = WhackRockPlugin(rpc_url, fund_address, private_key)
    
    functions = []
    
    # Get Current Composition
    functions.append(Function(
        fn_name="get_current_portfolio",
        fn_description="Get the current portfolio composition with weights in basis points",
        args=[],
        executable=lambda: _execute_function(plugin.get_current_composition)
    ))
    
    # Get Target Composition
    functions.append(Function(
        fn_name="get_target_portfolio",
        fn_description="Get the target portfolio composition with weights in basis points",
        args=[],
        executable=lambda: _execute_function(plugin.get_target_composition)
    ))
    
    # Get NAV
    functions.append(Function(
        fn_name="get_fund_nav",
        fn_description="Get the fund's total NAV in both WETH and USDC",
        args=[],
        executable=lambda: _execute_function(
            lambda: {
                'weth': plugin.get_total_nav_weth(),
                'usdc': plugin.get_total_nav_usdc()
            }
        )
    ))
    
    # Check Rebalance
    functions.append(Function(
        fn_name="check_rebalance_needed",
        fn_description="Check if portfolio rebalancing is needed based on deviation from targets",
        args=[],
        executable=lambda: _execute_function(plugin.calculate_rebalance_needed)
    ))
    
    # Set Weights
    functions.append(Function(
        fn_name="set_portfolio_weights",
        fn_description="Set target portfolio weights in basis points (must sum to 10000)",
        args=[
            Argument(
                name="weights",
                required=True,
                description="List of weights in basis points for each token in the portfolio"
            )
        ],
        executable=lambda weights: _execute_function(plugin.set_target_weights, weights)
    ))
    
    # Set Weights and Rebalance
    functions.append(Function(
        fn_name="set_weights_and_rebalance",
        fn_description="Set target weights and automatically rebalance if deviation threshold is met",
        args=[
            Argument(
                name="weights",
                required=True,
                description="List of weights in basis points for each token in the portfolio"
            )
        ],
        executable=lambda weights: _execute_function(plugin.set_weights_and_rebalance, weights)
    ))
    
    # Trigger Rebalance
    functions.append(Function(
        fn_name="rebalance_portfolio",
        fn_description="Manually trigger portfolio rebalancing",
        args=[],
        executable=lambda: _execute_function(plugin.trigger_rebalance)
    ))
    
    # Collect Fees
    functions.append(Function(
        fn_name="collect_management_fees",
        fn_description="Collect accrued management fees",
        args=[],
        executable=lambda: _execute_function(plugin.collect_management_fee)
    ))
    
    # Get Agent Info
    functions.append(Function(
        fn_name="get_agent_info",
        fn_description="Get current agent address and fee configuration",
        args=[],
        executable=lambda: _execute_function(plugin.get_agent_info)
    ))
    
    return functions


def _execute_function(func, *args, **kwargs):
    """Execute a function and return result in GAME SDK format."""
    try:
        result = func(*args, **kwargs)
        
        if isinstance(result, dict) and result.get('status') == 'error':
            return (
                FunctionResultStatus.FAILED,
                result.get('error', 'Unknown error'),
                result
            )
        
        return (
            FunctionResultStatus.DONE,
            "Function executed successfully",
            result
        )
    except Exception as e:
        return (
            FunctionResultStatus.FAILED,
            f"Error executing function: {str(e)}",
            {"error": str(e)}
        )


# Async wrapper for integration with async agents
async def get_whackrock_functions_async(rpc_url: str, fund_address: str, private_key: Optional[str] = None):
    """Async wrapper for getting WhackRock functions."""
    return get_whackrock_functions(rpc_url, fund_address, private_key)