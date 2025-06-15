"""
Example WhackRock Fund Management Agent

This example demonstrates how to create an AI agent that manages a WhackRock fund
using the GAME SDK and WhackRock plugin.
"""

import os
import asyncio
from game_sdk.game import Agent
from whackrock_plugin_gamesdk import get_whackrock_functions
from datetime import datetime


class WhackRockFundAgent(Agent):
    """AI Agent for managing WhackRock investment funds."""
    
    def __init__(self, fund_address: str, private_key: str, rpc_url: str = "https://mainnet.base.org"):
        super().__init__(
            name="WhackRock Fund Manager",
            instructions="""You are an AI fund manager for a WhackRock investment fund.
            Your goal is to maximize returns while managing risk appropriately.
            You should:
            1. Monitor portfolio composition and NAV
            2. Adjust weights based on market conditions
            3. Rebalance when deviations exceed threshold
            4. Collect management fees periodically
            """
        )
        
        # Initialize WhackRock functions
        self.fund_functions = get_whackrock_functions(
            rpc_url=rpc_url,
            fund_address=fund_address,
            private_key=private_key
        )
        
        # Add functions to agent
        for func in self.fund_functions:
            self.add_function(func)
        
        self.fund_address = fund_address
        self.last_rebalance = datetime.now()
        self.rebalance_cooldown_hours = 24  # Minimum hours between rebalances
    
    async def check_portfolio_health(self):
        """Check portfolio health and trigger rebalancing if needed."""
        print(f"[{datetime.now()}] Checking portfolio health...")
        
        # Get current composition
        current = await self.execute_function("get_current_portfolio")
        print(f"Current portfolio: {current}")
        
        # Check if rebalance is needed
        rebalance_check = await self.execute_function("check_rebalance_needed")
        print(f"Rebalance needed: {rebalance_check['needs_rebalance']}")
        
        if rebalance_check['needs_rebalance']:
            # Check cooldown
            hours_since_last = (datetime.now() - self.last_rebalance).total_seconds() / 3600
            if hours_since_last < self.rebalance_cooldown_hours:
                print(f"Rebalance cooldown active. Next rebalance in {self.rebalance_cooldown_hours - hours_since_last:.1f} hours")
                return
            
            print("Triggering rebalance...")
            result = await self.execute_function("rebalance_portfolio")
            print(f"Rebalance result: {result}")
            self.last_rebalance = datetime.now()
    
    async def adjust_risk_based_weights(self, risk_mode: str = "balanced"):
        """Adjust portfolio weights based on risk preference."""
        print(f"Adjusting weights for {risk_mode} risk mode...")
        
        if risk_mode == "conservative":
            # High USDC allocation
            weights = [2000, 2000, 6000]  # 20% WETH, 20% PRIME, 60% USDC
        elif risk_mode == "aggressive":
            # High volatile asset allocation
            weights = [4000, 5000, 1000]  # 40% WETH, 50% PRIME, 10% USDC
        else:  # balanced
            weights = [3500, 3500, 3000]  # 35% WETH, 35% PRIME, 30% USDC
        
        result = await self.execute_function("set_weights_and_rebalance", weights=weights)
        print(f"Weight adjustment result: {result}")
    
    async def collect_fees(self):
        """Collect management fees if available."""
        print("Collecting management fees...")
        result = await self.execute_function("collect_management_fees")
        print(f"Fee collection result: {result}")
    
    async def run_management_cycle(self):
        """Run a complete management cycle."""
        try:
            # 1. Get fund status
            nav = await self.execute_function("get_fund_nav")
            print(f"Fund NAV - WETH: {nav['weth']['nav_eth']:.4f}, USDC: ${nav['usdc']['nav_usdc']:,.2f}")
            
            # 2. Check portfolio health
            await self.check_portfolio_health()
            
            # 3. Collect fees (once per day)
            await self.collect_fees()
            
        except Exception as e:
            print(f"Error in management cycle: {e}")


async def main():
    """Main function to run the agent."""
    
    # Configuration (use environment variables in production)
    FUND_ADDRESS = os.getenv("WHACKROCK_FUND_ADDRESS", "0x...")
    PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY", "0x...")
    RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
    
    if FUND_ADDRESS == "0x..." or PRIVATE_KEY == "0x...":
        print("Please set WHACKROCK_FUND_ADDRESS and AGENT_PRIVATE_KEY environment variables")
        return
    
    # Create agent
    agent = WhackRockFundAgent(
        fund_address=FUND_ADDRESS,
        private_key=PRIVATE_KEY,
        rpc_url=RPC_URL
    )
    
    print(f"Starting WhackRock Fund Agent for {FUND_ADDRESS}")
    
    # Example 1: Run a single management cycle
    await agent.run_management_cycle()
    
    # Example 2: Adjust risk mode
    await agent.adjust_risk_based_weights("balanced")
    
    # Example 3: Continuous management loop
    # while True:
    #     await agent.run_management_cycle()
    #     await asyncio.sleep(3600)  # Run every hour


if __name__ == "__main__":
    asyncio.run(main())