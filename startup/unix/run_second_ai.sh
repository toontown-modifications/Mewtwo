#!/bin/sh
cd ../..

export DISTRICT_NAME="Sillyham"
export BASE_CHANNEL=402000000

while true
do
  python3 -m game.toontown.ai.AIStart config/Config.prc
  sleep 5
done