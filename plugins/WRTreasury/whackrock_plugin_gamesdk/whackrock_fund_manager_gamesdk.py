"""
WhackRock Fund Manager GAME SDK

This SDK provides a simple interface for interacting with the WhackRockFundV6_UniSwap_TWAP contract,
specifically for getting current/target weights and triggering rebalancing.
"""

from typing import Tuple, List, Dict, Any, Optional
from web3 import Web3
from web3.contract import Contract
import json
import os


class WhackRockFundManagerSDK:
    """SDK for interacting with WhackRock Fund smart contracts"""
    
    def __init__(
        self,
        web3_provider: str,
        fund_contract_address: str,
        private_key: Optional[str] = None,
        account_address: Optional[str] = None
    ):
        """
        Initialize the WhackRock Fund Manager SDK
        
        Args:
            web3_provider: Web3 RPC endpoint URL
            fund_contract_address: Address of the WhackRockFundV6 contract
            private_key: Private key for signing transactions (optional, for write operations)
            account_address: Account address (optional, for write operations)
        """
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        self.fund_address = Web3.to_checksum_address(fund_contract_address)
        self.private_key = private_key
        self.account_address = Web3.to_checksum_address(account_address) if account_address else None
        
        # Initialize contract with minimal ABI for the 3 main functions
        self.fund_abi = [
            {
                "inputs": [],
                "name": "getCurrentCompositionBPS",
                "outputs": [
                    {
                        "internalType": "uint256[]",
                        "name": "currentComposition_",
                        "type": "uint256[]"
                    },
                    {
                        "internalType": "address[]",
                        "name": "tokenAddresses_",
                        "type": "address[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getTargetCompositionBPS",
                "outputs": [
                    {
                        "internalType": "uint256[]",
                        "name": "targetComposition_",
                        "type": "uint256[]"
                    },
                    {
                        "internalType": "address[]",
                        "name": "tokenAddresses_",
                        "type": "address[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "triggerRebalance",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "agent",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "totalNAVInAccountingAsset",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "totalManagedAssets",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "totalNAVInUSDC",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "totalManagedAssetsInUSDC",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "uint256[]",
                        "name": "_weights",
                        "type": "uint256[]"
                    }
                ],
                "name": "setTargetWeights",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "uint256[]",
                        "name": "_weights",
                        "type": "uint256[]"
                    }
                ],
                "name": "setTargetWeightsAndRebalanceIfNeeded",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        self.fund_contract = self.w3.eth.contract(
            address=self.fund_address,
            abi=self.fund_abi
        )
    
    def get_current_weights(self) -> Dict[str, Any]:
        """
        Get the current composition of the fund's assets
        
        Returns:
            Dict containing:
                - token_addresses: List of token addresses
                - current_weights_bps: List of current weights in basis points (1 BPS = 0.01%)
                - current_weights_percent: List of current weights as percentages
                - tokens_with_weights: List of dicts with token address and weight info
        """
        try:
            # Call the contract function
            current_composition, token_addresses = self.fund_contract.functions.getCurrentCompositionBPS().call()
            
            # Convert weights from BPS to percentages
            current_weights_percent = [weight / 100 for weight in current_composition]
            
            # Create a combined list of tokens with their weights
            tokens_with_weights = []
            for i in range(len(token_addresses)):
                tokens_with_weights.append({
                    'token_address': token_addresses[i],
                    'weight_bps': current_composition[i],
                    'weight_percent': current_weights_percent[i]
                })
            
            return {
                'token_addresses': token_addresses,
                'current_weights_bps': current_composition,
                'current_weights_percent': current_weights_percent,
                'tokens_with_weights': tokens_with_weights
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'token_addresses': [],
                'current_weights_bps': [],
                'current_weights_percent': [],
                'tokens_with_weights': []
            }
    
    def get_target_weights(self) -> Dict[str, Any]:
        """
        Get the target composition of the fund's assets
        
        Returns:
            Dict containing:
                - token_addresses: List of token addresses
                - target_weights_bps: List of target weights in basis points (1 BPS = 0.01%)
                - target_weights_percent: List of target weights as percentages
                - tokens_with_weights: List of dicts with token address and weight info
        """
        try:
            # Call the contract function
            target_composition, token_addresses = self.fund_contract.functions.getTargetCompositionBPS().call()
            
            # Convert weights from BPS to percentages
            target_weights_percent = [weight / 100 for weight in target_composition]
            
            # Create a combined list of tokens with their weights
            tokens_with_weights = []
            for i in range(len(token_addresses)):
                tokens_with_weights.append({
                    'token_address': token_addresses[i],
                    'weight_bps': target_composition[i],
                    'weight_percent': target_weights_percent[i]
                })
            
            return {
                'token_addresses': token_addresses,
                'target_weights_bps': target_composition,
                'target_weights_percent': target_weights_percent,
                'tokens_with_weights': tokens_with_weights
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'token_addresses': [],
                'target_weights_bps': [],
                'target_weights_percent': [],
                'tokens_with_weights': []
            }
    
    def compare_weights(self) -> Dict[str, Any]:
        """
        Compare current weights with target weights to see deviations
        
        Returns:
            Dict containing weight comparison data for each token
        """
        try:
            current = self.get_current_weights()
            target = self.get_target_weights()
            
            if 'error' in current or 'error' in target:
                return {
                    'error': current.get('error', target.get('error')),
                    'comparisons': []
                }
            
            comparisons = []
            for i in range(len(current['token_addresses'])):
                current_bps = current['current_weights_bps'][i]
                target_bps = target['target_weights_bps'][i]
                deviation_bps = abs(current_bps - target_bps)
                
                comparisons.append({
                    'token_address': current['token_addresses'][i],
                    'current_weight_bps': current_bps,
                    'current_weight_percent': current['current_weights_percent'][i],
                    'target_weight_bps': target_bps,
                    'target_weight_percent': target['target_weights_percent'][i],
                    'deviation_bps': deviation_bps,
                    'deviation_percent': deviation_bps / 100,
                    'needs_rebalance': deviation_bps > 100  # 1% threshold
                })
            
            max_deviation_bps = max([c['deviation_bps'] for c in comparisons]) if comparisons else 0
            needs_rebalance = max_deviation_bps > 100
            
            return {
                'comparisons': comparisons,
                'max_deviation_bps': max_deviation_bps,
                'max_deviation_percent': max_deviation_bps / 100,
                'needs_rebalance': needs_rebalance
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'comparisons': []
            }
    
    def trigger_rebalance(self, gas_limit: int = 500000) -> Dict[str, Any]:
        """
        Trigger a rebalance of the fund's assets
        
        Args:
            gas_limit: Gas limit for the transaction (default: 500000)
            
        Returns:
            Dict containing transaction info or error
        """
        if not self.private_key or not self.account_address:
            return {
                'error': 'Private key and account address required for write operations',
                'success': False
            }
        
        try:
            # Check if caller is the agent
            agent_address = self.fund_contract.functions.agent().call()
            if self.account_address.lower() != agent_address.lower():
                return {
                    'error': f'Only the agent ({agent_address}) can trigger rebalance',
                    'success': False
                }
            
            # Build the transaction
            nonce = self.w3.eth.get_transaction_count(self.account_address)
            gas_price = self.w3.eth.gas_price
            
            transaction = self.fund_contract.functions.triggerRebalance().build_transaction({
                'from': self.account_address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price
            })
            
            # Sign and send the transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'tx_hash': receipt['transactionHash'].hex(),
                'gas_used': receipt['gasUsed'],
                'block_number': receipt['blockNumber'],
                'status': receipt['status']  # 1 for success, 0 for failure
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def set_target_weights(self, weights_bps: List[int], rebalance_if_needed: bool = False, gas_limit: int = 500000) -> Dict[str, Any]:
        """
        Set new target weights for the fund's assets
        
        Args:
            weights_bps: List of target weights in basis points (must sum to 10000)
            rebalance_if_needed: If True, uses setTargetWeightsAndRebalanceIfNeeded
            gas_limit: Gas limit for the transaction (default: 500000)
            
        Returns:
            Dict containing transaction info or error
        """
        if not self.private_key or not self.account_address:
            return {
                'error': 'Private key and account address required for write operations',
                'success': False
            }
        
        # Validate weights sum to 10000 (100%)
        total_weight = sum(weights_bps)
        if total_weight != 10000:
            return {
                'error': f'Weights must sum to 10000 basis points (100%), got {total_weight}',
                'success': False
            }
        
        try:
            # Check if caller is the agent
            agent_address = self.fund_contract.functions.agent().call()
            if self.account_address.lower() != agent_address.lower():
                return {
                    'error': f'Only the agent ({agent_address}) can set target weights',
                    'success': False
                }
            
            # Build the transaction
            nonce = self.w3.eth.get_transaction_count(self.account_address)
            gas_price = self.w3.eth.gas_price
            
            # Choose function based on rebalance_if_needed parameter
            if rebalance_if_needed:
                transaction = self.fund_contract.functions.setTargetWeightsAndRebalanceIfNeeded(weights_bps).build_transaction({
                    'from': self.account_address,
                    'nonce': nonce,
                    'gas': gas_limit,
                    'gasPrice': gas_price
                })
            else:
                transaction = self.fund_contract.functions.setTargetWeights(weights_bps).build_transaction({
                    'from': self.account_address,
                    'nonce': nonce,
                    'gas': gas_limit,
                    'gasPrice': gas_price
                })
            
            # Sign and send the transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'tx_hash': receipt['transactionHash'].hex(),
                'gas_used': receipt['gasUsed'],
                'block_number': receipt['blockNumber'],
                'status': receipt['status'],  # 1 for success, 0 for failure
                'weights_set': weights_bps,
                'rebalanced': rebalance_if_needed
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def get_fund_info(self) -> Dict[str, Any]:
        """
        Get general information about the fund
        
        Returns:
            Dict containing fund information
        """
        try:
            agent = self.fund_contract.functions.agent().call()
            nav_weth = self.fund_contract.functions.totalNAVInAccountingAsset().call()
            nav_usdc = self.fund_contract.functions.totalNAVInUSDC().call()
            
            return {
                'fund_address': self.fund_address,
                'agent_address': agent,
                'total_nav_weth': nav_weth,
                'total_nav_weth_formatted': self.w3.from_wei(nav_weth, 'ether'),
                'total_nav_usdc': nav_usdc,
                'total_nav_usdc_formatted': nav_usdc / 1e6  # USDC has 6 decimals
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'fund_address': self.fund_address
            }


# Helper functions for GAME SDK integration
def create_fund_manager_functions(sdk: WhackRockFundManagerSDK) -> List[Dict[str, Any]]:
    """
    Create function definitions for GAME SDK integration
    
    Args:
        sdk: Instance of WhackRockFundManagerSDK
        
    Returns:
        List of function definitions for GAME SDK action space
    """
    from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus
    
    def get_current_weights(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """Get current asset weights of the fund"""
        result = sdk.get_current_weights()
        if 'error' in result:
            return FunctionResultStatus.FAILED, f"Failed to get current weights: {result['error']}", {}
        
        message = "Current fund composition:\n"
        for token in result['tokens_with_weights']:
            message += f"- {token['token_address']}: {token['weight_percent']:.2f}%\n"
        
        return FunctionResultStatus.DONE, message, result
    
    def get_target_weights(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """Get target asset weights of the fund"""
        result = sdk.get_target_weights()
        if 'error' in result:
            return FunctionResultStatus.FAILED, f"Failed to get target weights: {result['error']}", {}
        
        message = "Target fund composition:\n"
        for token in result['tokens_with_weights']:
            message += f"- {token['token_address']}: {token['weight_percent']:.2f}%\n"
        
        return FunctionResultStatus.DONE, message, result
    
    def check_rebalance_needed(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """Check if the fund needs rebalancing"""
        result = sdk.compare_weights()
        if 'error' in result:
            return FunctionResultStatus.FAILED, f"Failed to compare weights: {result['error']}", {}
        
        if result['needs_rebalance']:
            message = f"Rebalance needed! Max deviation: {result['max_deviation_percent']:.2f}%\n"
            message += "Token deviations:\n"
            for comp in result['comparisons']:
                if comp['deviation_percent'] > 0.1:  # Only show deviations > 0.1%
                    message += f"- {comp['token_address']}: {comp['deviation_percent']:.2f}%\n"
        else:
            message = f"No rebalance needed. Max deviation: {result['max_deviation_percent']:.2f}%"
        
        return FunctionResultStatus.DONE, message, result
    
    def trigger_rebalance(gas_limit: int = 500000, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """Trigger a rebalance of the fund"""
        result = sdk.trigger_rebalance(gas_limit)
        if not result['success']:
            return FunctionResultStatus.FAILED, f"Failed to trigger rebalance: {result['error']}", result
        
        message = f"Rebalance triggered successfully!\n"
        message += f"Transaction hash: {result['tx_hash']}\n"
        message += f"Gas used: {result['gas_used']}"
        
        return FunctionResultStatus.DONE, message, result
    
    def set_target_weights(weights_bps: str, rebalance_if_needed: bool = False, gas_limit: int = 500000, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """Set new target weights for the fund"""
        try:
            # Parse weights from comma-separated string to list of integers
            weights_list = [int(w.strip()) for w in weights_bps.split(',')]
        except ValueError:
            return FunctionResultStatus.FAILED, "Invalid weights format. Use comma-separated integers (e.g., '5000,3000,2000')", {}
        
        result = sdk.set_target_weights(weights_list, rebalance_if_needed, gas_limit)
        if not result['success']:
            return FunctionResultStatus.FAILED, f"Failed to set target weights: {result['error']}", result
        
        message = f"Target weights updated successfully!\n"
        message += f"New weights: {result['weights_set']}\n"
        message += f"Transaction hash: {result['tx_hash']}\n"
        message += f"Gas used: {result['gas_used']}"
        if result['rebalanced']:
            message += "\nRebalancing was triggered automatically."
        
        return FunctionResultStatus.DONE, message, result
    
    def get_fund_info(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """Get general fund information"""
        result = sdk.get_fund_info()
        if 'error' in result:
            return FunctionResultStatus.FAILED, f"Failed to get fund info: {result['error']}", {}
        
        message = f"Fund Information:\n"
        message += f"- Address: {result['fund_address']}\n"
        message += f"- Agent: {result['agent_address']}\n"
        message += f"- Total NAV (WETH): {result['total_nav_weth_formatted']:.4f} WETH\n"
        message += f"- Total NAV (USDC): ${result['total_nav_usdc_formatted']:,.2f}"
        
        return FunctionResultStatus.DONE, message, result
    
    # Create Function objects for GAME SDK
    functions = [
        Function(
            fn_name="get_current_weights",
            fn_description="Get the current asset weights/composition of the fund",
            args=[],
            executable=get_current_weights
        ),
        Function(
            fn_name="get_target_weights",
            fn_description="Get the target asset weights/composition of the fund",
            args=[],
            executable=get_target_weights
        ),
        Function(
            fn_name="check_rebalance_needed",
            fn_description="Check if the fund needs rebalancing by comparing current vs target weights",
            args=[],
            executable=check_rebalance_needed
        ),
        Function(
            fn_name="trigger_rebalance",
            fn_description="Trigger a rebalance of the fund's assets to match target weights",
            args=[
                Argument(
                    name="gas_limit",
                    type="integer",
                    description="Gas limit for the transaction (default: 500000)"
                )
            ],
            executable=trigger_rebalance
        ),
        Function(
            fn_name="set_target_weights",
            fn_description="Set new target weights for the fund's assets",
            args=[
                Argument(
                    name="weights_bps",
                    type="string",
                    description="Comma-separated list of weights in basis points (e.g., '5000,3000,2000' for 50%, 30%, 20%)"
                ),
                Argument(
                    name="rebalance_if_needed",
                    type="boolean",
                    description="If true, automatically rebalance after setting weights (default: false)"
                ),
                Argument(
                    name="gas_limit",
                    type="integer",
                    description="Gas limit for the transaction (default: 500000)"
                )
            ],
            executable=set_target_weights
        ),
        Function(
            fn_name="get_fund_info",
            fn_description="Get general information about the fund (address, agent, NAV)",
            args=[],
            executable=get_fund_info
        )
    ]
    
    return functions
