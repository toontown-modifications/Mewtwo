dc-file otpd/dclass/toon.dc
dc-file otpd/dclass/otp.dc
server-version sv1.0.47.38
server-base-channel 1000000
air-stateserver 4002
air-base-channel 401000000
air-channel-allocation 999999
account-bridge-file otpd/databases/accounts.json

# DClass:
dc-multiple-inheritance #t
dc-sort-virtual-inheritance #t
dc-sort-inheritance-by-file #t

want-gardening true
want-randomized-hats false
want-membership true
want-cogdominiums true
want-coderedemption true
want-server-debugging false
want-do-live-updates true
want-delivery-manager false
want-server-maintenance false
want-discord-integration true
active-holidays 60, 61, 62, 63, 64, 65, 66
buildings-server-data-folder backups/buildings

max-code-redemption-attempts 5

model-path game/resources