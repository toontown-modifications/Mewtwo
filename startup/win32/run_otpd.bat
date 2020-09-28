@echo off
cd ../../otpd

:main
otp_server.exe --loglevel info --pretty config/otpd.yml
pause
goto :main