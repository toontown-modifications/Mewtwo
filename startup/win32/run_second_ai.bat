@echo off
cd ../..

set DISTRICT_NAME=Nutty River
set BASE_CHANNEL=402000000
set /P PYTHON_PATH=<PYTHON_PATH

cls

:main
%PYTHON_PATH% -m game.toontown.ai.AIStart config/Config.prc
pause
goto :main