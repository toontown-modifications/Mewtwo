@echo off
title OTP Server - Non ExtAgent
cd ../../otpd

:main
otp_server.exe --loglevel info --pretty config/otpd_nonext.yml
pause
goto :main