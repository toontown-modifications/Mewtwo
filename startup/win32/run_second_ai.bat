@echo off
cd ../..

set DISTRICT_NAME=Nutty River
set BASE_CHANNEL=402000000

cls

:main
C:/Panda3D-1.11.0-x64-astron/python/python -m game.toontown.ai.AIStart config/Config.prc
pause
goto :main