import logging
from typing import List, cast
from game.worker import Worker # type: ignore
from game.game_functions import game_function # type: ignore
from game.types import BigNumber, Address # type: ignore

# Assuming signal.py is in the same directory (package) or discoverable
from .signal import derive_weights, NUM_LLM_SIGNAL_ASSETS

# Configuration for the specific WhackRockFund instance this worker manages
# IMPORTANT: Replace with your actual deployed fund address
VAULT_ADDRESS = Address("0xReplaceWithYourWhackRockFundAddress")

# The "BenFan" strategy, as per the signal.py, is for a conceptual set of assets
# (e.g., stETH, WBTC, USDT, or generic Asset1, Asset2, Asset3).
# The worker needs to manage a WhackRockFund instance.
# CRUCIAL: The number of assets in the LLM signal (NUM_LLM_SIGNAL_ASSETS)
# MUST match the number of `allowedTokens` in the `VAULT_ADDRESS`.
# The order of weights from `derive_weights` will be applied to the
# `allowedTokens` of the fund in their existing order.

# Example:
# If NUM_LLM_SIGNAL_ASSETS = 3 and derive_weights() returns [0.6, 0.3, 0.1]
# And the fund at VAULT_ADDRESS has allowedTokens = [USDC_ADDR, CBETH_ADDR, VIRTU_ADDR]
# Then target for USDC will be 6000 BPS, CBETH 3000 BPS, VIRTU 1000 BPS.

class BenFanWorker(Worker):
    @game_function(schedule="0 */1 * * *") # Runs at the start of every hour
    async def manage_fund_portfolio(self):
        logging.info(f"BenFanWorker: Starting fund management cycle for VAULT: {VAULT_ADDRESS}")

        try:
            # 1. Get current fund composition (weights, addresses, symbols)
            logging.info(f"BenFanWorker: Fetching current composition for {VAULT_ADDRESS}...")
            current_comp_data = await self.virtual.enact_action_from_name(
                action_name="whackrock_get_current_composition", # From whackrock_fund_manager_gamesdk
                args_dict={"fund_address": VAULT_ADDRESS}
            )
            # Expected: Tuple[List[BigNumber], List[Address], List[str]]
            current_weights_bps_bn: List[BigNumber] = cast(List[BigNumber], current_comp_data[0])
            token_addresses: List[Address] = cast(List[Address], current_comp_data[1])
            token_symbols: List[str] = cast(List[str], current_comp_data[2])

            num_fund_assets = len(token_addresses)
            logging.info(f"BenFanWorker: Fund {VAULT_ADDRESS} has {num_fund_assets} allowed assets: {token_symbols} ({token_addresses})")
            logging.info(f"BenFanWorker: Current BPS weights: {[w.value for w in current_weights_bps_bn]}")


            if num_fund_assets == 0:
                logging.warning(f"BenFanWorker: Fund {VAULT_ADDRESS} has no allowed tokens. Cannot manage.")
                return

            if num_fund_assets != NUM_LLM_SIGNAL_ASSETS:
                logging.error(
                    f"BenFanWorker: Mismatch! Fund has {num_fund_assets} assets, "
                    f"but LLM signal is configured for {NUM_LLM_SIGNAL_ASSETS} assets. "
                    f"Please check NUM_LLM_SIGNAL_ASSETS in signal.py and fund configuration."
                )
                return

            # 2. Get target weights signal from the LLM
            logging.info("BenFanWorker: Deriving target weights from LLM signal...")
            target_weights_float: List[float] = await derive_weights()

            if not target_weights_float or len(target_weights_float) != num_fund_assets:
                logging.error(
                    f"BenFanWorker: Failed to derive valid target weights or length mismatch. "
                    f"Expected {num_fund_assets}, got {len(target_weights_float) if target_weights_float else 'None'}. Skipping cycle."
                )
                return
            logging.info(f"BenFanWorker: Derived target float weights (signal order): {target_weights_float}")

            # 3. Convert target float weights to BPS, ensuring sum is 10000
            # Assumes sum(target_weights_float) is 1.0 due to normalization in derive_weights()
            target_weights_bps_list: List[BigNumber] = []
            
            if num_fund_assets == 0: # Should have been caught by earlier check
                logging.warning("BenFanWorker: num_fund_assets is 0 during BPS conversion, skipping BPS list generation.")
            else:
                target_weights_bps_list_int: List[int] = [0] * num_fund_assets
                
                # Step A: Calculate exact BPS values (as floats) - sum should be 10000.0
                # max(0.0, w_float) ensures no negative weights proceed from LLM signal if it misbehaves
                exact_bps_values: List[float] = [max(0.0, w_float) * 10000.0 for w_float in target_weights_float]

                # Step B: Get the integer part (floor)
                for i in range(num_fund_assets):
                    target_weights_bps_list_int[i] = int(exact_bps_values[i]) # floor is implicit

                # Step C: Calculate sum of floored BPS values (will be <= 10000 if sum of floats is 1.0)
                current_sum_bps = sum(target_weights_bps_list_int)

                # Step D: Calculate positive remainder to distribute
                remainder_to_distribute = 10000 - current_sum_bps
                
                logging.info(
                    f"BenFanWorker: BPS Normalization - Input Floats (sum {sum(target_weights_float):.4f}): {target_weights_float}, "
                    f"ExactBPS (sum {sum(exact_bps_values):.2f}): {[f'{v:.2f}' for v in exact_bps_values]}, "
                    f"FlooredBPS: {target_weights_bps_list_int}, SumFloored: {current_sum_bps}, "
                    f"RemainderToDistribute: {remainder_to_distribute}"
                )

                if remainder_to_distribute > 0:
                    # Distribute the positive remainder based on largest fractional parts
                    # Create a list of (fractional_part, original_index)
                    fractional_parts_with_indices = []
                    for i in range(num_fund_assets):
                        fractional_part = exact_bps_values[i] - float(target_weights_bps_list_int[i])
                        fractional_parts_with_indices.append((fractional_part, i))
                    
                    # Sort by fractional part in descending order
                    fractional_parts_with_indices.sort(key=lambda x: x[0], reverse=True)

                    # Add 1 BPS to the weights with the largest fractional parts
                    for i in range(remainder_to_distribute):
                        if i < len(fractional_parts_with_indices): # Safety check
                            index_to_increment = fractional_parts_with_indices[i][1]
                            target_weights_bps_list_int[index_to_increment] += 1
                        else: # Should not happen if remainder is small (e.g. < num_fund_assets)
                            logging.warning(f"BenFanWorker: Remainder to distribute ({remainder_to_distribute}) exceeds number of assets to distribute to. Iteration {i}.")
                            break 
                elif remainder_to_distribute < 0:
                    # This case indicates an issue: sum of floats was > 1.0 or calculation error.
                    # signal.py's derive_weights() aims to make sum of floats exactly 1.0.
                    logging.error(
                        f"BenFanWorker: Negative remainder ({remainder_to_distribute}) during BPS normalization. "
                        f"This suggests input float weights did not sum to 1.0 as expected. "
                        f"Floats: {target_weights_float}, Sum: {sum(target_weights_float)}. "
                        f"Proceeding with potentially incorrect BPS sum."
                    )
                    # Optionally, could attempt a forced reduction here, but it masks an upstream problem.
                
                target_weights_bps_list = [BigNumber(bps) for bps in target_weights_bps_list_int]

            # Final verification log
            final_sum_check = sum(w.value for w in target_weights_bps_list)
            if final_sum_check != 10000 and num_fund_assets > 0:
                logging.error(
                    f"BenFanWorker: CRITICAL - BPS weights do NOT sum to 10000 after normalization. "
                    f"Final sum: {final_sum_check}. Weights: {[w.value for w in target_weights_bps_list]}."
                )
                # At this point, if the sum is still off, it's a more fundamental issue with the logic or inputs.
                # The agent might choose to not proceed or use a safe fallback.
                # For this example, we'll log the error and it will proceed with the calculated (potentially incorrect sum) weights.

            logging.info(f"BenFanWorker: Calculated target BPS weights (fund order, sum {final_sum_check}): {[w.value for w in target_weights_bps_list]}")


            # 4. Compare current and target weights to decide if rebalance is needed
            deviation_threshold_float = 0.02 # e.g., 2% deviation for any single asset
            needs_explicit_rebalance_decision = False
            max_abs_deviation_float = 0.0

            if len(current_weights_bps_bn) == num_fund_assets and len(target_weights_float) == num_fund_assets :
                for i in range(num_fund_assets):
                    current_w_float = float(current_weights_bps_bn[i].value) / 10000.0
                    target_w_f = target_weights_float[i] # Using the normalized floats from signal
                    
                    abs_deviation = abs(current_w_float - target_w_f)
                    if abs_deviation > max_abs_deviation_float:
                        max_abs_deviation_float = abs_deviation
                    
                    if abs_deviation > deviation_threshold_float:
                        needs_explicit_rebalance_decision = True
            else:
                logging.warning("BenFanWorker: Length mismatch during deviation check. Skipping agent-side deviation check.")


            logging.info(f"BenFanWorker: Max absolute float deviation observed: {max_abs_deviation_float*100:.2f}%. Agent's rebalance trigger threshold: {needs_explicit_rebalance_decision}")

            target_comp_data = await self.virtual.enact_action_from_name(
                action_name="whackrock_get_target_composition", # from whackrock_fund_manager_gamesdk
                args_dict={"fund_address": VAULT_ADDRESS}
            )
            fund_current_target_weights_bps_bn: List[BigNumber] = cast(List[BigNumber], target_comp_data[0])

            targets_are_different = False
            if len(fund_current_target_weights_bps_bn) == len(target_weights_bps_list):
                for i in range(len(target_weights_bps_list)):
                    if fund_current_target_weights_bps_bn[i].value != target_weights_bps_list[i].value:
                        targets_are_different = True
                        break
            else: 
                targets_are_different = True # Lengths differ, so targets are different

            if not targets_are_different and not needs_explicit_rebalance_decision:
                logging.info("BenFanWorker: New target weights match fund's current targets, and current composition is within agent's threshold. No action.")
                return

            # 5. Set new target weights and let the contract decide on rebalancing
            logging.info(f"BenFanWorker: Targets changed or deviation significant. Calling setTargetWeightsAndRebalanceIfNeeded.")

            set_rebalance_args = {
                "fund_address": VAULT_ADDRESS,
                "weights_bps": target_weights_bps_list
            }
            
            tx_result_str = await self.virtual.enact_action_from_name(
                action_name="whackrock_set_weights_and_rebalance", # from whackrock_fund_manager_gamesdk
                args_dict=set_rebalance_args
            )
            logging.info(f"BenFanWorker: `setTargetWeightsAndRebalanceIfNeeded` action submitted. Result: {tx_result_str}")

        except Exception as e:
            logging.error(f"BenFanWorker: Critical error during fund management cycle: {e}", exc_info=True)

