"""
BenFan Agent Worker - Manages WhackRock fund based on Benjamin Cowen's analysis and tweets about it.
"""

import logging
import os
from typing import List, cast, Optional
from game.worker import Worker  # type: ignore
from game.game_functions import game_function  # type: ignore
from game.types import BigNumber, Address  # type: ignore
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin  # type: ignore

# Import our enhanced signal module
from .signal import derive_weights, NUM_LLM_SIGNAL_ASSETS, get_last_analysis

# Configuration for the specific WhackRockFund instance this worker manages
# IMPORTANT: Replace with your actual deployed fund address
VAULT_ADDRESS = Address(os.environ.get("WHACKROCK_FUND_ADDRESS", "0xReplaceWithYourWhackRockFundAddress"))

# Twitter configuration
TWITTER_ENABLED = os.environ.get("TWITTER_ENABLED", "true").lower() == "true"
GAME_TWITTER_ACCESS_TOKEN = os.environ.get("GAME_TWITTER_ACCESS_TOKEN")

# Asset symbols for tweet generation
ASSET_SYMBOLS = ["VIRTUAL", "cbBTC", "USDC"]

class BenFanWorker(Worker):
    def __init__(self):
        super().__init__()
        self.twitter_client = None
        
        # Initialize Twitter client if enabled
        if TWITTER_ENABLED and GAME_TWITTER_ACCESS_TOKEN:
            try:
                options = {
                    "credentials": {
                        "game_twitter_access_token": GAME_TWITTER_ACCESS_TOKEN
                    }
                }
                twitter_plugin = TwitterPlugin(options)
                self.twitter_client = twitter_plugin.twitter_client
                logging.info("BenFanWorker: Twitter integration initialized")
            except Exception as e:
                logging.error(f"BenFanWorker: Failed to initialize Twitter: {e}")
                self.twitter_client = None
    
    @game_function(schedule="0 0 * * *")  # Runs daily at midnight UTC
    async def check_for_new_videos(self):
        """Check for new Benjamin Cowen videos and update weights if found."""
        logging.info("BenFanWorker: Checking for new Benjamin Cowen videos...")
        
        try:
            # This will process new videos and update the processed_videos.json
            weights = await derive_weights()
            logging.info(f"BenFanWorker: Video check complete. Current weights: {weights}")
        except Exception as e:
            logging.error(f"BenFanWorker: Error checking for new videos: {e}")
    
    @game_function(schedule="0 */1 * * *")  # Runs at the start of every hour
    async def manage_fund_portfolio(self):
        """Main fund management cycle with Twitter integration."""
        logging.info(f"BenFanWorker: Starting fund management cycle for VAULT: {VAULT_ADDRESS}")

        try:
            # 1. Get current fund composition
            logging.info(f"BenFanWorker: Fetching current composition for {VAULT_ADDRESS}...")
            current_comp_data = await self.virtual.enact_action_from_name(
                action_name="whackrock_get_current_composition",
                args_dict={"fund_address": VAULT_ADDRESS}
            )
            
            current_weights_bps_bn: List[BigNumber] = cast(List[BigNumber], current_comp_data[0])
            token_addresses: List[Address] = cast(List[Address], current_comp_data[1])
            token_symbols: List[str] = cast(List[str], current_comp_data[2])

            num_fund_assets = len(token_addresses)
            logging.info(f"BenFanWorker: Fund has {num_fund_assets} assets: {token_symbols}")
            logging.info(f"BenFanWorker: Current BPS weights: {[w.value for w in current_weights_bps_bn]}")

            if num_fund_assets == 0:
                logging.warning(f"BenFanWorker: Fund {VAULT_ADDRESS} has no allowed tokens.")
                return

            if num_fund_assets != NUM_LLM_SIGNAL_ASSETS:
                logging.error(
                    f"BenFanWorker: Mismatch! Fund has {num_fund_assets} assets, "
                    f"but signal expects {NUM_LLM_SIGNAL_ASSETS} assets."
                )
                return

            # 2. Get target weights from signal
            logging.info("BenFanWorker: Deriving target weights from signal...")
            target_weights_float: List[float] = await derive_weights()

            if not target_weights_float or len(target_weights_float) != num_fund_assets:
                logging.error(f"BenFanWorker: Invalid target weights. Skipping cycle.")
                return
                
            logging.info(f"BenFanWorker: Target weights (float): {target_weights_float}")

            # 3. Convert to BPS with proper normalization
            target_weights_bps_list = self._convert_to_bps(target_weights_float)
            logging.info(f"BenFanWorker: Target weights (BPS): {[w.value for w in target_weights_bps_list]}")

            # 4. Check if rebalance is needed
            current_weights_float = [float(w.value) / 10000.0 for w in current_weights_bps_bn]
            max_deviation = max(
                abs(current_weights_float[i] - target_weights_float[i]) 
                for i in range(num_fund_assets)
            )
            
            deviation_threshold = 0.02  # 2% threshold
            needs_rebalance = max_deviation > deviation_threshold
            
            logging.info(f"BenFanWorker: Max deviation: {max_deviation*100:.2f}%, Needs rebalance: {needs_rebalance}")

            # 5. Get current target weights from fund
            target_comp_data = await self.virtual.enact_action_from_name(
                action_name="whackrock_get_target_composition",
                args_dict={"fund_address": VAULT_ADDRESS}
            )
            fund_target_weights_bps: List[BigNumber] = cast(List[BigNumber], target_comp_data[0])

            # Check if targets have changed
            targets_changed = any(
                fund_target_weights_bps[i].value != target_weights_bps_list[i].value
                for i in range(len(target_weights_bps_list))
            )

            if not targets_changed and not needs_rebalance:
                logging.info("BenFanWorker: No rebalance needed.")
                return

            # 6. Execute rebalance
            logging.info("BenFanWorker: Executing rebalance...")
            
            old_weights_pct = [f"{w*100:.1f}%" for w in current_weights_float]
            new_weights_pct = [f"{w*100:.1f}%" for w in target_weights_float]
            
            tx_result = await self.virtual.enact_action_from_name(
                action_name="whackrock_set_weights_and_rebalance",
                args_dict={
                    "fund_address": VAULT_ADDRESS,
                    "weights_bps": target_weights_bps_list
                }
            )
            logging.info(f"BenFanWorker: Rebalance transaction submitted: {tx_result}")

            # 7. Post tweet about rebalance
            if self.twitter_client and TWITTER_ENABLED:
                await self._post_rebalance_tweet(
                    old_weights_pct, 
                    new_weights_pct,
                    max_deviation
                )

        except Exception as e:
            logging.error(f"BenFanWorker: Critical error during fund management: {e}", exc_info=True)

    def _convert_to_bps(self, weights_float: List[float]) -> List[BigNumber]:
        """Convert float weights to BPS ensuring sum is exactly 10000."""
        num_assets = len(weights_float)
        
        # Calculate exact BPS values
        exact_bps = [max(0.0, w) * 10000.0 for w in weights_float]
        
        # Floor to integers
        bps_int = [int(bps) for bps in exact_bps]
        
        # Calculate remainder
        current_sum = sum(bps_int)
        remainder = 10000 - current_sum
        
        # Distribute remainder to assets with largest fractional parts
        if remainder > 0:
            fractional_parts = [(exact_bps[i] - bps_int[i], i) for i in range(num_assets)]
            fractional_parts.sort(reverse=True)
            
            for i in range(min(remainder, num_assets)):
                idx = fractional_parts[i][1]
                bps_int[idx] += 1
        
        return [BigNumber(bps) for bps in bps_int]

    async def _post_rebalance_tweet(
        self, 
        old_weights: List[str], 
        new_weights: List[str],
        max_deviation: float
    ):
        """Post a tweet about the rebalance."""
        try:
            # Get the latest video analysis for context
            analysis = await get_last_analysis()
            
            if analysis:
                # Tweet with video context
                tweet_text = (
                    f"🎯 WhackRock Fund Rebalanced!\n\n"
                    f"Based on @intothecryptoverse latest: \"{analysis.video_title}\"\n\n"
                    f"Market view: {analysis.macro_tone.upper()} | Risk: {analysis.risk_on_off.upper()}\n\n"
                    f"Old → New weights:\n"
                    f"• $VIRTUAL: {old_weights[0]} → {new_weights[0]}\n"
                    f"• $cbBTC: {old_weights[1]} → {new_weights[1]}\n"
                    f"• $USDC: {old_weights[2]} → {new_weights[2]}\n\n"
                    f"{analysis.analysis_summary}\n\n"
                    f"#DeFi #WhackRock #BenCowen"
                )
            else:
                # Fallback tweet without video context
                tweet_text = (
                    f"🎯 WhackRock Fund Rebalanced!\n\n"
                    f"Portfolio adjusted (deviation: {max_deviation*100:.1f}%)\n\n"
                    f"Old → New weights:\n"
                    f"• $VIRTUAL: {old_weights[0]} → {new_weights[0]}\n"
                    f"• $cbBTC: {old_weights[1]} → {new_weights[1]}\n"
                    f"• $USDC: {old_weights[2]} → {new_weights[2]}\n\n"
                    f"Managed by BenFan Agent 🤖\n\n"
                    f"#DeFi #WhackRock #Crypto"
                )
            
            # Ensure tweet is within character limit
            if len(tweet_text) > 280:
                # Truncate analysis summary if needed
                tweet_text = tweet_text[:277] + "..."
            
            # Post the tweet
            result = self.twitter_client.create_tweet(text=tweet_text)
            tweet_id = result["data"]["id"]
            logging.info(f"BenFanWorker: Tweet posted successfully: https://x.com/i/web/status/{tweet_id}")
            
        except Exception as e:
            logging.error(f"BenFanWorker: Failed to post tweet: {e}")

# Entry point for the worker
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    worker = BenFanWorker()
    logging.info("BenFan Worker initialized and ready") 