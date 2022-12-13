# Starts up all the services using screen all in one go.
# Currently only supports Unix based systems.

import sys, os, time

isProduction = '--prod' in sys.argv

os.chdir('startup/unix')

if sys.platform == 'linux':
    os.system('screen -dmS OTP ./run_otpd.sh')
else:
    os.system('screen -dms OTP ./run_otpd_darwin.sh')

os.system('screen -dmS External ./run_server_ext.sh')

# Wait until the external server starts.
time.sleep(25)

# os.system('cd ../.. && screen -dmS Districts python3 -m DistrictStarter')
os.system('screen -dmS Sillyville ./run_first_ai.sh')
os.system('screen -dmS Sillyham ./run_second_ai.sh')
# os.system('screen -dmS Crazyham ./run_third_ai.sh')

if isProduction:
    os.system('screen -dmS Stunnel ./run_stunnel.sh')
    os.system('screen -dmS Endpoints ./run_endpoint_manager.sh')

    os.system('cd ../../../discord-status-bot && python3 -m Starter')