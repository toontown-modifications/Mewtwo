@echo off
cd ../..

set USE_EXT_AGENT=1
set /P PYTHON_PATH=<PYTHON_PATH

:main
%PYTHON_PATH% -m game.toontown.uberdog.ServerStart config/Config.prc
pause
goto :main