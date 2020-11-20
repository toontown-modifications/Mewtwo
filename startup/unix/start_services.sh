#!/bin/sh
cd ../..

screen -S OTP -X quit

python3 -m ServerStarter
