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
want-randomized-hats false
want-membership true
want-cogdominiums true
want-coderedemption true
want-do-live-updates true
want-discord-integration true
want-parties true
want-instant-parties true
want-loyalty-requirement true
want-ds-anydbm true
want-token-expirations false
want-system-responses true

# Turning this off fixes parties for TTO Clients that use midi audio
want-ogg-music true

# Code Redemption
max-code-redemption-attempts 5

# Backups
buildings-server-data-folder backups/buildings
store-server-data-folder backups/store
secret-friend-storage backups/friendCodes/secrets.json
bingo-server-data-folder backups/bingo

# Whitelist
whitelist-url http://download.sunrise.games/launcher/
whitelist-stage-dir game/whitelist

# Resources
model-path game/resources
