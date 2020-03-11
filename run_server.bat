@echo off

:main
C:/Panda3D-1.11.0-x64-astron/python/python -m server.ServerStart config/Config.prc
pause
goto :main