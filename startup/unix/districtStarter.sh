#!/bin/sh
cd ../..

while true
do
  python3 -m game.toontown.ai.AIStart config/Config.prc
  sleep 5
done