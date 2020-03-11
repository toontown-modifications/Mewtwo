@echo off
cd astron

:main
astrond.exe config/astrond.yml --pretty
pause
goto :main