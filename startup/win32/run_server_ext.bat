@echo off
cd ../..



set NO_EXT_AGENT=0

:main
python -m game.toontown.uberdog.ServerStart config/Config.prc
pause
goto :main