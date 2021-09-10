#!/bin/sh
cd ../..

export DISTRICT_NAME="Zany Acres"
export BASE_CHANNEL=403000000

screen -dmS "Zany Acres" python3 -m game.toontown.ai.AIStart config/Config.prc
