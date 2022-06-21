#!/bin/sh
cd ../..

export DISTRICT_NAME="Nutty River"
export BASE_CHANNEL=403000000

screen -dmS "$DISTRICT_NAME" python3 -m game.toontown.ai.AIStart config/Config.prc