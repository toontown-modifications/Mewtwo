cd ../..

set DISTRICT_NAME=%~1 %~2

set BASE_CHANNEL=%~3

title %DISTRICT_NAME%

:main
C:/Panda3D-1.11.0-x64-astron/python/python -m game.toontown.ai.AIStart config/Config.prc
pause
goto :main