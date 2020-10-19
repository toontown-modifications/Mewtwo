#!/bin/sh
cd ../..

export DISTRICT_NAME="Sillyville"
export BASE_CHANNEL=401000000

python3 -m game.toontown.ai.AIStart config/Config.prc