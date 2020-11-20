#!/bin/sh
cd ../..

export USE_EXT_AGENT=0

python3 -m game.toontown.uberdog.ServerStart config/Config.prc
