# Starts up all the services using screen all in one go.
# Currently only supports Unix based systems.

import sys, os, time

isProduction = '--prod' in sys.argv

os.chdir('startup/unix')

if sys.platform in ('linux', 'linux2'):
    os.system('screen -dmS OTP ./run_otpd.sh')
else:
    os.system('screen -dms OTP ./run_otpd_darwin.sh')

os.system('screen -dmS External ./run_server_ext.sh')

# Wait until the external server starts.
time.sleep(5)

os.system('screen -dmS Sillyville ./run_first_ai.sh')

# Wait until the first AI starts.
time.sleep(10)

os.system('screen -dmS "Nutty River" ./run_second_ai.sh')

if isProduction:
    os.system('screen -dmS Stunnel ./run_stunnel.sh')
    os.system('screen -dmS Endpoints ./run_endpoint_manager.sh')

    os.system('cd ../../../discord-status-bot && python3 -m Starter')