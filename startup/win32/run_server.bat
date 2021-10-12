@echo off
title Server - Non ExtAgent
cd ../..

set USE_EXT_AGENT=0
set /P PYTHON_PATH=<PYTHON_PATH

:main
%PYTHON_PATH% -m game.toontown.uberdog.ServerStart config/Config.prc
pause
goto :main