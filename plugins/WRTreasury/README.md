
© 2025 WhackRock Labs Ltd. All rights reserved.

**Agent template (Python)** 
reusable, permission‑less treasury layer on top of GAME.

Goal in one sentence
Build an open‑source system where WhackRock allocates capital to many autonomous agent vaults, each of which runs its own strategy, holds a tokenised treasury, and pays an automatic 80 / 20 fee split (80 % to the agent’s dev wallet, 20 % to WRK stakers).

## 💡 Project Overview

| Layer | What we’re delivering |
|-------|-----------------------|

| **Treasury factory** | One click → deploy a new **ERC‑4626** vault that trades only assets you whitelist, charges an up‑front management fee, and auto‑splits fees **80 / 20** (dev / WRK‑stakers). https://github.com/WhackRock/whackrock-treasury-template|
| **Agent template (Python)** | A ~50‑line GAME Worker that grabs data (e.g., YouTube transcripts), calculates new weights, and calls the vault’s `rebalance()`. Anyone can fork it and launch a strategy. |
| **Uniswap adapters & oracle** | On‑chain Uniswap‑V3 TWAP oracle + Universal Router wrapper, so every vault can swap any whitelisted token on **Base**—no off‑chain keepers required. |
| **Subgraph** | Records one share‑price per day for each vault, giving anyone a trust‑less time‑series for Sharpe‑ratio calculations. |


game-python/
└─ plugins/
   └─ whackrock-treasury/
      ├─ README.md
      ├─ pyproject.toml            ← local install:  pip install -e .
      ├─ whackrock_treasury_plugin_gamesdk/
      │   ├─ __init__.py           ← registers Game‑SDK functions
      │   ├─ treasury.py           ← Web3 helpers (ERC‑4626 vault)
      │   └─ uniswap.py            ← Universal‑Router calldata helper
      └─ examples/
          ├─ benfan_agent/
          │   ├─ worker.py
          │   └─ signals.py
          └─ template_agent/
              ├─ worker.py
              └─ signals.py


# 🏦 WhackRock Treasury Plugin for `game-python`

* Interact with any **WeightedTreasuryVault** clone on Base  
* One‑call helpers for `get_weights`, `set_weights`, and `rebalance`  
* Universal‑Router swap builder (Uniswap V3)  
* 80 / 20 fee split logic is inside the vault, so the plugin focuses on weights

```bash
# quick start
cd game-python/plugins/whackrock-treasury
pip install -e .
game run examples/benfan_agent/worker.py
