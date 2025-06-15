"""
Example WhackRock Fund Worker

This example demonstrates a worker that performs automated fund management tasks
including signal-based rebalancing and performance monitoring.
"""

import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from game_sdk.game import Worker
from whackrock_plugin_gamesdk import WhackRockPlugin
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from example.signal import derive_weights  # Import the signal module


class WhackRockFundWorker(Worker):
    """Worker for automated WhackRock fund management tasks."""
    
    def __init__(self, fund_address: str, private_key: str, rpc_url: str = "https://mainnet.base.org"):
        super().__init__(name="WhackRock Fund Worker")
        
        # Initialize plugin
        self.plugin = WhackRockPlugin(
            rpc_url=rpc_url,
            fund_address=fund_address,
            private_key=private_key
        )
        
        self.fund_address = fund_address
        self.performance_history = []
        
    async def run_signal_based_rebalance(self):
        """Run rebalancing based on external signals (Benjamin Cowen analysis)."""
        print(f"[{datetime.now()}] Running signal-based rebalance...")
        
        try:
            # Get signal weights from Benjamin Cowen analysis
            signal_weights = await derive_weights()
            print(f"Signal weights received: {signal_weights}")
            
            # Convert to basis points (assuming 3 assets: VIRTUAL, cbBTC, USDC)
            weights_bps = [int(w * 10000) for w in signal_weights]
            
            # Ensure weights sum to exactly 10000
            weight_sum = sum(weights_bps)
            if weight_sum != 10000:
                # Adjust last weight to make sum exactly 10000
                weights_bps[-1] += 10000 - weight_sum
            
            print(f"Setting weights (bps): {weights_bps}")
            
            # Set weights and rebalance
            result = self.plugin.set_weights_and_rebalance(weights_bps)
            
            if result['status'] == 'success':
                print(f"Rebalance successful! Transaction: {result['transaction']['transactionHash']}")
            else:
                print(f"Rebalance failed: {result['error']}")
                
        except Exception as e:
            print(f"Error in signal-based rebalance: {e}")
    
    async def monitor_performance(self):
        """Monitor and log fund performance metrics."""
        print(f"[{datetime.now()}] Monitoring fund performance...")
        
        try:
            # Get NAV
            nav_weth = self.plugin.get_total_nav_weth()
            nav_usdc = self.plugin.get_total_nav_usdc()
            
            # Get composition
            composition = self.plugin.get_current_composition()
            
            # Create performance snapshot
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'nav_weth': nav_weth['nav_eth'] if nav_weth['status'] == 'success' else 0,
                'nav_usdc': nav_usdc['nav_usdc'] if nav_usdc['status'] == 'success' else 0,
                'composition': composition['composition'] if composition['status'] == 'success' else []
            }
            
            self.performance_history.append(snapshot)
            
            # Calculate performance if we have history
            if len(self.performance_history) > 1:
                prev = self.performance_history[-2]
                curr = self.performance_history[-1]
                
                usdc_change = curr['nav_usdc'] - prev['nav_usdc']
                pct_change = (usdc_change / prev['nav_usdc'] * 100) if prev['nav_usdc'] > 0 else 0
                
                print(f"Performance Update:")
                print(f"  NAV (USDC): ${curr['nav_usdc']:,.2f} ({pct_change:+.2f}%)")
                print(f"  NAV (WETH): {curr['nav_weth']:.4f}")
                print(f"  Portfolio:")
                for asset in curr['composition']:
                    print(f"    {asset['symbol']}: {asset['weight_percent']:.1f}%")
            
            # Save performance history
            self._save_performance_history()
            
        except Exception as e:
            print(f"Error monitoring performance: {e}")
    
    def _save_performance_history(self):
        """Save performance history to file."""
        filename = f"performance_{self.fund_address[:8]}.json"
        with open(filename, 'w') as f:
            json.dump(self.performance_history[-100:], f, indent=2)  # Keep last 100 snapshots
    
    async def check_and_collect_fees(self):
        """Check and collect management fees if due."""
        print(f"[{datetime.now()}] Checking management fees...")
        
        try:
            # Get agent info
            agent_info = self.plugin.get_agent_info()
            
            if agent_info['status'] == 'success':
                last_collection = agent_info['last_fee_collection_timestamp']
                current_time = int(datetime.now().timestamp())
                days_since_collection = (current_time - last_collection) / 86400
                
                print(f"Days since last fee collection: {days_since_collection:.1f}")
                
                # Collect if more than 7 days
                if days_since_collection > 7:
                    print("Collecting fees...")
                    result = self.plugin.collect_management_fee()
                    
                    if result['status'] == 'success':
                        print(f"Fees collected! Transaction: {result['transaction']['transactionHash']}")
                    else:
                        print(f"Fee collection failed: {result['error']}")
                else:
                    print(f"Fees not due yet. Next collection in {7 - days_since_collection:.1f} days")
                    
        except Exception as e:
            print(f"Error checking fees: {e}")
    
    async def emergency_check(self):
        """Perform emergency checks for unusual conditions."""
        print(f"[{datetime.now()}] Running emergency checks...")
        
        try:
            # Check for extreme deviations
            rebalance_check = self.plugin.calculate_rebalance_needed()
            
            if rebalance_check['status'] == 'success':
                max_deviation = rebalance_check['max_deviation_percent']
                
                if max_deviation > 10:  # 10% deviation is concerning
                    print(f"⚠️  WARNING: Large deviation detected: {max_deviation:.1f}%")
                    print("Deviations by asset:")
                    for dev in rebalance_check['deviations']:
                        print(f"  {dev['symbol']}: {dev['deviation_percent']:.1f}%")
                    
                    # Could trigger emergency rebalance here
                    # result = self.plugin.trigger_rebalance()
            
        except Exception as e:
            print(f"Error in emergency check: {e}")
    
    async def run_cycle(self):
        """Run a complete worker cycle."""
        print(f"\n{'='*60}")
        print(f"WhackRock Fund Worker Cycle - {datetime.now()}")
        print(f"{'='*60}")
        
        # 1. Monitor performance
        await self.monitor_performance()
        
        # 2. Check for emergency conditions
        await self.emergency_check()
        
        # 3. Check and collect fees
        await self.check_and_collect_fees()
        
        # 4. Run signal-based rebalance (once per day at specific time)
        current_hour = datetime.now().hour
        if current_hour == 14:  # 2 PM UTC
            await self.run_signal_based_rebalance()


async def main():
    """Main function to run the worker."""
    
    # Configuration
    FUND_ADDRESS = os.getenv("WHACKROCK_FUND_ADDRESS", "0x...")
    PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY", "0x...")
    RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
    
    if FUND_ADDRESS == "0x..." or PRIVATE_KEY == "0x...":
        print("Please set WHACKROCK_FUND_ADDRESS and AGENT_PRIVATE_KEY environment variables")
        return
    
    # Create worker
    worker = WhackRockFundWorker(
        fund_address=FUND_ADDRESS,
        private_key=PRIVATE_KEY,
        rpc_url=RPC_URL
    )
    
    print(f"Starting WhackRock Fund Worker for {FUND_ADDRESS}")
    
    # Run continuously
    while True:
        try:
            await worker.run_cycle()
        except Exception as e:
            print(f"Error in worker cycle: {e}")
        
        # Run every 30 minutes
        await asyncio.sleep(1800)


if __name__ == "__main__":
    # Ensure we have required environment variables for signal module
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Signal-based rebalancing will use fallback weights.")
    
    asyncio.run(main())