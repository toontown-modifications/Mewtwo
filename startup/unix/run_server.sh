#!/bin/sh
cd ../..

export USE_EXT_AGENT=0

python2 -m game.toontown.uberdog.ServerStart config/Config.prc
