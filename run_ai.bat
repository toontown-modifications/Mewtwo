@echo off

rem Get the user input:
set /P DISTRICT_NAME="District name (DEFAULT: Sillyville): " || ^
set DISTRICT_NAME=Sillyville
set /P BASE_CHANNEL="Base channel (DEFAULT: 401000000): " || ^
set BASE_CHANNEL=401000000

cls

:main
C:/Panda3D-1.11.0-x64-astron/python/python -m game.toontown.ai.AIStart config/Config.prc
pause
goto :main