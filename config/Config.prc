# Internal
dc-file otpd/dclass/toon.dc
dc-file otpd/dclass/otp.dc

server-version sv1.0.47.38

server-base-channel 1000000
air-stateserver 4002
air-base-channel 401000000
air-channel-allocation 999999

# External
account-bridge-file otpd/databases/accounts.json

api-token QrLEtq3CCWEax3M2
server-type prod

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

# Code Redemption
max-code-redemption-attempts 5

# Backups
buildings-server-data-folder backups/buildings
store-server-data-folder backups/store

# Whitelist
whitelist-url http://cdn.toontown.disney.go.com/toontown/en/
whitelist-stage-dir game/whitelist

# Discord
discord-logins-webhook https://canary.discord.com/api/webhooks/765666107326726184/BiSkGsHVPqKwMqPo-2jx4fCvwMFe-57qLCldT4ZX0ZK35oq4Z60G7PCaJtpNyC0pfkdp
discord-approvals-webhook https://canary.discord.com/api/webhooks/765665770465394712/eBp9-TdUW6Nvh32LY8EyzwFIFQ2P5iQ3CjPmKSMqFjEkUkeRARiR9QLuirlnCvKcGw3e
discord-reports-webhook https://canary.discord.com/api/webhooks/765666597402443817/1GQTu5DMXshx_l7jakEy9sCsDSgRPMFSqABx0adXrWgpxRaa64O4KyVD-QC0Qv_5JFoM
discord-invasions-webhook https://canary.discord.com/api/webhooks/777891732577845299/xQI3Bdn4Ww2nvuuvSxVIcR0AF1yD3lny1T3bjlnDxsTM0dsuYPDIMFU838vYFl1s7Sa-
discord-integration-sig SOB0GLTKBTlpqt0O4nUiwl1EMlKVz6x5

# Resources
model-path game/resources