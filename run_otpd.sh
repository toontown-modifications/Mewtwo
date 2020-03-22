#!/bin/sh
cd otpd

wine otp_server.exe --loglevel info config/otpd.yml
