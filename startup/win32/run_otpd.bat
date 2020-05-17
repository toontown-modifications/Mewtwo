@echo off
cd ../../otpd

:main
otp_server.exe --loglevel info config/otpd.yml
pause
goto :main