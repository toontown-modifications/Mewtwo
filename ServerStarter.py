# Starts up all the services using screen all in one go.
# Currently only supports Unix based systems.

import os

os.chdir('startup/unix')

os.system('screen -dmS OTP ./run_otpd.sh')
os.system('screen -dmS External ./run_server_ext.sh')
os.system('screen -dmS AI ./run_ai.sh')
os.system('screen -dmS Stunnel ./run_stunnel.sh')
os.system('screen -dmS Endpoints ./run_endpoint_manager.sh')