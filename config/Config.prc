# Internal
dc-file otpd/dclass/toon.dc
dc-file otpd/dclass/otp.dc

server-version sv1.0.47.38

server-base-channel 1000000
air-stateserver 4002
air-base-channel 401000000
air-channel-allocation 999999
eventlog-host 127.0.0.1:7197

# External
account-bridge-file otpd/databases/accounts.json

server-type dev

# Features
want-gardening true
want-randomized-hats false
want-membership true
want-cogdominiums true
want-coderedemption true
want-do-live-updates true
want-discord-integration true
want-parties false
want-instant-parties true
want-welcome-valley false
want-fireworks-cannons false
want-loyalty-requirement true
want-ds-anydbm false
want-token-expirations false

# Code Redemption
max-code-redemption-attempts 5

# Backups
buildings-server-data-folder backups/buildings
store-server-data-folder backups/store

# Whitelist
whitelist-url http://cdn.toontown.disney.go.com/toontown/en/
whitelist-stage-dir game/whitelist

# Resources
model-path game/resources