from panda3d.core import loadPrcFile
import requests

# Load our configuration.
loadPrcFile('../../config/local.prc')

banEndpoint = 'https://127.0.0.1/bans/BanAccount.php'

username = eval(input('Username: '))
reason = eval(input('Reason for Ban: '))

# If you truly need this key, ask Rocket.
secretKey = config.GetString('api-token')

headers = {
    'User-Agent': 'Sunrise Games - AccountBanner'
}

data = {
    'username': username,
    'banReason': reason,
    'secretKey': secretKey
}

request = requests.post(banEndpoint, data, headers = headers).text
print(request)