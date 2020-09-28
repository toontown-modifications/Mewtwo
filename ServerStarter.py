# Starts up the OTP/External/AI server with screen all in one go.
# Currently only supports Unix based systems.

import os

os.chdir('startup/unix')

os.system('screen -dmS OTP ./run_otpd.sh')
os.system('screen -dmS External ./run_server_ext.sh')
os.system('screen -dmS AI ./run_ai.sh')