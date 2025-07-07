# BenFan: WhackRock Fund Rebalancing Agent

BenFan is a minimal example agent that demonstrates how to use the WhackRock Fund Manager GAME SDK to automatically rebalance a fund based on signals. This example showcases the integration between signal generation, the GAME SDK, and the WhackRock Fund smart contract.

## Overview

BenFan consists of two main components:
1. **Signal Generator** (`signal.py`) - Generates target allocation weights
2. **Worker Agent** (`worker.py`) - Executes rebalancing based on signals

The agent performs a single, focused task: **automatically rebalance a WhackRock fund when instructed**, using the `set_target_weights` function with `rebalance_if_needed=True` to update allocations and trigger rebalancing in one atomic transaction.

## How It Works

### Signal Generation (`signal.py`)

The signal generator provides target portfolio weights using a simple time-based rotation strategy:

- **Conservative** (50%, 30%, 20%) - Low-risk allocation
- **Balanced** (40%, 40%, 20%) - Moderate allocation
- **Aggressive** (60%, 25%, 15%) - High-risk allocation  
- **Equal Weight** (33.33%, 33.33%, 33.34%) - Diversified allocation

The signal rotates every minute, making it easy to observe rebalancing in action during testing.

```python
def get_target_weights_bps() -> List[int]:
    """Returns weights in basis points (BPS) that sum to 10000 (100%)"""
    current_minute = int(time.time() / 60) % 4
    
    if current_minute == 0:
        return [5000, 3000, 2000]  # Conservative: 50%, 30%, 20%
    elif current_minute == 1:
        return [4000, 4000, 2000]  # Balanced: 40%, 40%, 20%
    # ... etc
```

### Worker Agent (`worker.py`)

The worker is a GAME SDK agent with a single function: `rebalance_fund()`. When executed, it:

1. **Gets the current signal** from `signal.py`
2. **Calls the fund manager SDK** to set new target weights
3. **Triggers automatic rebalancing** using `rebalance_if_needed=True`
4. **Reports transaction results** including hash and gas usage

```python
def rebalance_fund(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    # Get current signal
    target_weights_bps = get_target_weights_bps()
    
    # Set weights and rebalance in one transaction
    result = fund_sdk.set_target_weights(
        weights_bps=target_weights_bps,
        rebalance_if_needed=True,  # Triggers automatic rebalancing
        gas_limit=800000
    )
    
    # Return results
    return FunctionResultStatus.DONE, success_message, result
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   signal.py     │    │   worker.py     │    │  Smart Contract │
│                 │    │                 │    │                 │
│ • Time-based    │───▶│ • GAME SDK      │───▶│ • WhackRock     │
│   rotation      │    │   Worker        │    │   Fund V6       │
│ • Returns BPS   │    │ • Single action │    │ • Rebalancing   │
│   weights       │    │ • Auto-rebalance│    │   logic         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Configuration

Before running BenFan, update the configuration variables in `worker.py`:

```python
# Configuration - Replace with your actual values
WEB3_PROVIDER = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"
FUND_CONTRACT_ADDRESS = "0x..."  # Your fund contract address
AGENT_PRIVATE_KEY = "0x..."      # Agent's private key (keep secure!)
AGENT_ADDRESS = "0x..."          # Agent's address
```

Also ensure you have the required environment variable:
```bash
export GAME_API_KEY="your_game_api_key"
```

## Usage

### Testing the Signal
```bash
cd game-python-WR-package/plugins/WRTreasury/example/benfan
python signal.py
```

### Running the Worker
```bash
python worker.py
```

### Integration with Larger Systems
```python
from benfan.worker import create_rebalance_worker

# Create and run the worker
worker = create_rebalance_worker()
result = worker.run("Please rebalance the fund based on the current signal")
```

## Key Features

### ✅ Minimal Design
- **Single responsibility**: Only rebalances funds
- **Simple signal**: Time-based rotation for easy testing
- **Clear separation**: Signal generation separate from execution

### ✅ Robust Integration  
- **GAME SDK compatibility**: Follows standard Worker patterns
- **Error handling**: Comprehensive error reporting and recovery
- **State tracking**: Maintains history of rebalancing operations

### ✅ Production Ready
- **Atomic operations**: Uses `setTargetWeightsAndRebalanceIfNeeded` for safety
- **Gas optimization**: Configurable gas limits
- **Transaction monitoring**: Full transaction result reporting

## Example Output

When BenFan successfully rebalances a fund:

```
Fund rebalanced successfully!
Signal: Aggressive allocation: 60.0%, 25.0%, 15.0%
New weights (BPS): [6000, 2500, 1500]
Transaction hash: 0x1234567890abcdef...
Gas used: 542,123
```

## Extending BenFan

BenFan is designed as a starting point. You can extend it by:

### Signal Enhancement
- Replace time-based rotation with real market data
- Add technical indicators or external APIs
- Implement more sophisticated allocation strategies

### Worker Capabilities  
- Add monitoring and alerting functions
- Implement risk management checks
- Add portfolio analytics and reporting

### Advanced Features
- Multi-fund management
- Dynamic risk adjustment
- Integration with external data sources

## Dependencies

- **GAME SDK**: For autonomous agent functionality
- **WhackRock Fund Manager SDK**: For fund interaction
- **Web3.py**: For blockchain interaction
- **Standard Library**: `time`, `typing`, `os`

## Security Notes

⚠️ **Important Security Considerations:**

1. **Private Key Management**: Never commit private keys to version control
2. **Agent Authorization**: Ensure only authorized agents can rebalance funds
3. **Gas Limits**: Set appropriate gas limits to prevent stuck transactions
4. **Signal Validation**: Validate signal outputs before applying to funds

## License

This example is part of the WhackRock ecosystem and follows the same licensing terms as the parent project.

---

**BenFan demonstrates the power of combining signal generation with autonomous agents for decentralized fund management. Use it as a foundation for building more sophisticated fund management strategies.**