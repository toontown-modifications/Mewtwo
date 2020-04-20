@echo off

set NO_EXT_AGENT=0

:main
C:/Panda3D-1.11.0-x64-astron/python/python -m server.ServerStart config/Config.prc
pause
goto :main