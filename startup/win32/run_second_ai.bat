@echo off
cd ../..

set DISTRICT_NAME=Nutty River
set BASE_CHANNEL=402000000

cls

:main
python -m game.toontown.ai.AIStart config/Config.prc
pause
goto :main