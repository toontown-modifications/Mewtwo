@echo off
for /r %%f in (*.pyc) do (C:/Panda3D-1.11.0-x64-astron/python/Scripts/uncompyle6.exe -o "%%~df%%~pf%%~nf.py" "%%~df%%~pf%%~nf.pyc")
pause