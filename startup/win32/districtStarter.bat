@echo off
cd ../..

title %DISTRICT_NAME%

:main
python -m game.toontown.ai.AIStart config/Config.prc
pause
goto :main