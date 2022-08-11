#!/bin/sh
cd ../..

export DISTRICT_NAME="Crazyham"
export BASE_CHANNEL=403000000

while true
do
  python3 -m game.toontown.ai.AIStart config/Config.prc
  sleep 5
done