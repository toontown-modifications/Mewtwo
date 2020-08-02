@echo off
cd ../../otpd

:main
otp_server.exe --loglevel info config/otpd_nonext.yml
pause
goto :main