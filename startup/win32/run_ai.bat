@echo off
cd ../..

rem Get the user input:
set /P DISTRICT_NAME="District name (DEFAULT: Sillyville): " || ^
set DISTRICT_NAME=Sillyville
set /P BASE_CHANNEL="Base channel (DEFAULT: 401000000): " || ^
set BASE_CHANNEL=401000000
set /P PYTHON_PATH=<PYTHON_PATH

cls

title %DISTRICT_NAME%

:main
%PYTHON_PATH% -m game.toontown.ai.AIStart config/Config.prc
pause
goto :main