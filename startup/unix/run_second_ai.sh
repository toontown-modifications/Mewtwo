#!/bin/sh
cd ../..

export DISTRICT_NAME="Nutty River"
export BASE_CHANNEL=402000000

python2 -m game.toontown.ai.AIStart config/Config.prc