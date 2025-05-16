from web3 import Web3, AsyncWeb3
from typing import List, Dict, Any, Union, Optional, Tuple
from decimal import Decimal
import json
import asyncio
import os

from .config import (
    get_rpc_url, 
    VAULT_ABI_SNIPPET, 
    ORACLE_ABI_SNIPPET, 
    DEFAULT_TOKENS,
    DEFAULT_VAULT_ADDRESS,
    REBALANCE_THRESHOLD_BPS
)
from .utils import logger

class Treasury:
    """
    User-friendly interface to interact with WeightedTreasuryVault contracts
    
    Features:
    - Get current weights and targets
    - Set new target weights
    - Rebalance the portfolio
    - Get asset information and balances
    - Calculate optimal rebalance swaps
    """
    def __init__(self, address: Optional[str] = None, signer_key: Optional[str] = None):
        """
        Initialize a Treasury manager
        
        Args:
            address: The address of the vault contract (or None to use DEFAULT_VAULT_ADDRESS)
            signer_key: Optional private key for signing transactions
        """
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(get_rpc_url()))
        
        # Use provided address or default from environment
        if address is None:
            if DEFAULT_VAULT_ADDRESS is None:
                raise ValueError("No vault address provided and TREASURY_VAULT_ADDRESS not set in environment")
            address = DEFAULT_VAULT_ADDRESS
            logger.info(f"Using default vault address from environment: {address}")
        
        self.address = Web3.to_checksum_address(address)
        self.vault = self.w3.eth.contract(address=self.address, abi=VAULT_ABI_SNIPPET)
        
        # Set up signer if provided
        self.signer = None
        if signer_key:
            logger.debug("Initializing signer")
            self.signer = self.w3.eth.account.from_key(signer_key)
            logger.info(f"Signer address: {self.signer.address}")
        else:
            # Check environment for signer key
            signer_key_env = os.environ.get("TREASURY_SIGNER_KEY")
            if signer_key_env:
                logger.debug("Using signer key from environment")
                self.signer = self.w3.eth.account.from_key(signer_key_env)
                logger.info(f"Signer address from environment: {self.signer.address}")

    async def get_weights(self) -> List[int]:
        """
        Get the current target weights from the vault
        
        Returns:
            List of weights in basis points (100 = 1%)
        """
        try:
            logger.debug(f"Getting weights from vault: {self.address}")
            weights = await self.vault.functions.targetWeights().call()
            logger.info(f"Current weights: {weights}")
            return weights
        except Exception as e:
            logger.error(f"Failed to get target weights: {e}")
            raise ValueError(f"Failed to get target weights: {e}")

    async def get_asset_info(self) -> Dict[str, Any]:
        """
        Get information about the vault's assets
        
        Returns:
            Dictionary with asset addresses, balances, and weights
        """
        # This would require additional contract calls to get asset list
        # Simplified version for now
        weights = await self.get_weights()
        return {
            "weights": weights,
            "total_weight": sum(weights)
        }

    async def is_rebalance_needed(
        self, 
        new_weights: List[int], 
        threshold_bps: int = REBALANCE_THRESHOLD_BPS
    ) -> bool:
        """
        Check if rebalance is needed based on weight difference
        
        Args:
            new_weights: New target weights (in basis points)
            threshold_bps: Threshold for rebalance in basis points (default from env or 200)
            
        Returns:
            True if rebalance is needed, False otherwise
        """
        logger.debug(f"Checking if rebalance needed (threshold: {threshold_bps} bps)")
        curr_weights = await self.get_weights()
        if len(curr_weights) != len(new_weights):
            msg = f"New weights length ({len(new_weights)}) does not match current weights ({len(curr_weights)})"
            logger.error(msg)
            raise ValueError(msg)
            
        # Check if any weight differs by more than threshold
        for i, (c, n) in enumerate(zip(curr_weights, new_weights)):
            deviation = abs(c - n)
            if deviation > threshold_bps:
                logger.info(f"Rebalance needed: asset {i} deviation {deviation} bps > threshold {threshold_bps} bps")
                return True
                
        logger.info("No rebalance needed, all weights within threshold")
        return False
        
    async def set_weights(self, weights: List[int]) -> str:
        """
        Set new target weights
        
        Args:
            weights: New weights in basis points (must sum to 10000)
            
        Returns:
            Transaction hash
        """
        if not self.signer:
            logger.error("No signer provided for transaction")
            raise ValueError("Signer key required for transaction")
            
        # Validate weights
        if sum(weights) != 10000:
            msg = f"Weights must sum to 10000, got {sum(weights)}"
            logger.error(msg)
            raise ValueError(msg)
        
        logger.info(f"Setting weights to: {weights}")
            
        # Build transaction
        tx = await self.vault.functions.setWeights(weights).build_transaction({
            "from": self.signer.address,
            "nonce": await self.w3.eth.get_transaction_count(self.signer.address),
        })
        
        # Sign and send
        signed = self.signer.sign_transaction(tx)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        logger.info(f"Set weights transaction sent: {tx_hash_hex}")
        return tx_hash_hex

    async def set_and_rebalance(self, weights: List[int], swap_data: bytes) -> str:
        """
        Set new weights and rebalance in two transactions
        
        Args:
            weights: New target weights (in basis points)
            swap_data: Encoded swap data for the rebalance
            
        Returns:
            Transaction hash of the rebalance transaction
        """
        if not self.signer:
            logger.error("No signer provided for transactions")
            raise ValueError("Signer key required for transactions")

        # Set weights first
        try:
            logger.info(f"Setting weights to {weights} and rebalancing")
            tx1 = await self.vault.functions.setWeights(weights).build_transaction({
                "from": self.signer.address,
                "nonce": await self.w3.eth.get_transaction_count(self.signer.address)
            })
            
            signed1 = self.signer.sign_transaction(tx1)
            tx_hash1 = await self.w3.eth.send_raw_transaction(signed1.rawTransaction)
            tx_hash1_hex = tx_hash1.hex()
            logger.info(f"Set weights transaction sent: {tx_hash1_hex}")
            
            # Wait for the first transaction to be mined
            logger.debug("Waiting for weights transaction to be mined...")
            receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash1, timeout=120)
            if receipt.status != 1:
                msg = f"setWeights transaction failed: {tx_hash1_hex}"
                logger.error(msg)
                raise ValueError(msg)
            
            logger.info("Weights set successfully, now rebalancing")
            
            # Now rebalance
            tx2 = await self.vault.functions.rebalance(swap_data).build_transaction({
                "from": self.signer.address,
                "nonce": await self.w3.eth.get_transaction_count(self.signer.address),
                "gas": 2_400_000
            })
            
            signed2 = self.signer.sign_transaction(tx2)
            tx_hash2 = await self.w3.eth.send_raw_transaction(signed2.rawTransaction)
            tx_hash2_hex = tx_hash2.hex()
            logger.info(f"Rebalance transaction sent: {tx_hash2_hex}")
            
            return tx_hash2_hex
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise ValueError(f"Transaction failed: {e}")

    @staticmethod
    def resolve_token_address(token: str) -> str:
        """
        Resolve token symbol to address using the DEFAULT_TOKENS mapping
        
        Args:
            token: Token symbol or address
            
        Returns:
            Token address
        """
        if token in DEFAULT_TOKENS:
            return DEFAULT_TOKENS[token]
        return Web3.to_checksum_address(token)
