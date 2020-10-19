#!/bin/sh
cd ../..

export NO_EXT_AGENT=1

python3 -m game.toontown.uberdog.ServerStart config/Config.prc
