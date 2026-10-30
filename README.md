# FutureSight

A Gen 9 Random Battle bot for Pokémon Showdown, comparing MCTS and expectiminimax. Built for a COP3530

## Setup

Requirements: Python 3.11+, Node.js, Rust (from https://rustup.rs).

1. Clone Pokémon Showdown next to this repo (not inside it) and start it:

   ```
   git clone https://github.com/smogon/pokemon-showdown.git
   cd pokemon-showdown
   npm install
   cp config/config-example.js config/config.js
   node pokemon-showdown start --no-security
   ```

   Leave this terminal open.

2. In a second terminal, set up this repo:

   Clone the repo

   ```
   git clone https://github.com/parkinw-sys/FutureSight.git
   cd FutureSight
   ```

   Create a Python venv

   ```macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   ```Windows (powershell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   Install Python dependencies

   ```
   pip install -r requirements.txt
   pip install poke-engine --config-settings="build-args=--features poke-engine/gen9,poke-engine/terastallization --no-default-features"
   ```

3. Check it works:
   ```
   python main.py
   ```
   It should play one battle between two random bots and print the result.
