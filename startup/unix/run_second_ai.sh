#!/bin/sh
cd ../..

export DISTRICT_NAME="Sillyham"
export BASE_CHANNEL=402000000

screen -dmS "$DISTRICT_NAME" python3 -m game.toontown.ai.AIStart config/Config.prc