#!/bin/sh
cd ../..

export DISTRICT_NAME="Sillyville"
export BASE_CHANNEL=401000000

python2 -m game.toontown.ai.AIStart config/Config.prc