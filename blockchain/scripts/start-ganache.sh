#!/bin/bash

# FlightChain - Ganache Startup Script
# This script starts a local Ganache blockchain for development

echo "========================================"
echo "  FlightChain - Starting Ganache"
echo "========================================"

# Configuration
PORT=8545
NETWORK_ID=5777
MNEMONIC="myth like bonus scare over problem client lizard pioneer submit female collect"
ACCOUNTS=10
DEFAULT_BALANCE=100

echo ""
echo "Configuration:"
echo "  Port: $PORT"
echo "  Network ID: $NETWORK_ID"
echo "  Accounts: $ACCOUNTS"
echo "  Default Balance: $DEFAULT_BALANCE ETH"
echo ""

# Check if ganache is installed
if ! command -v ganache &> /dev/null; then
    echo "Error: Ganache is not installed."
    echo "Please run: npm install -g ganache"
    exit 1
fi

# Start Ganache with deterministic accounts for reproducible testing
ganache \
    --port $PORT \
    --networkId $NETWORK_ID \
    --deterministic \
    --accounts $ACCOUNTS \
    --defaultBalanceEther $DEFAULT_BALANCE \
    --mnemonic "$MNEMONIC" \
    --gasLimit 6721975 \
    --gasPrice 20000000000 \
    --verbose

echo ""
echo "Ganache stopped."
