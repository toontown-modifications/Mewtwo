@echo off
cd ../..

set USE_EXT_AGENT=1

:main
python -m game.toontown.uberdog.ServerStart config/Config.prc
pause
goto :main