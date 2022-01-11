@echo off
title OTP Server - ExtAgent (MongoDB)
cd ../../otpd

:main
otp_server.exe --loglevel info --pretty config/otpd_mongo.yml
pause
goto :main