@echo off
cd ../..

set NO_EXT_AGENT=1

:main
C:/Panda3D-1.11.0-x64-astron/python/python -m game.toontown.uberdog.ServerStart config/Config.prc
pause
goto :main