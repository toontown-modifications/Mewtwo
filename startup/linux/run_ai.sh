#!/bin/sh
cd ../..

# Get the user input:
read -p "District name (DEFAULT: Sillyville): " DISTRICT_NAME
export DISTRICT_NAME=${DISTRICT_NAME:-Sillyville}
read -p "Base channel (DEFAULT: 401000000): " BASE_CHANNEL
export BASE_CHANNEL=${BASE_CHANNEL:-401000000}

python -m game.toontown.ai.AIStart config/Config.prc
