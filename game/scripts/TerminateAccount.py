from panda3d.core import loadPrcFile
import requests

# Load our configuration.
loadPrcFile('../../config/local.prc')

terminateEndpoint = 'https://toontastic.sunrise.games/bans/TerminateAccount.php'

username = eval(input('Username: '))
reason = 'Violated rules multiple times.'

# If you truly need this key, ask Rocket.
secretKey = config.GetString('api-token')

headers = {
    'User-Agent': 'Sunrise Games - TerminateAccount'
}

data = {
    'username': username,
    'reason': reason,
    'secretKey': secretKey
}

request = requests.post(terminateEndpoint, data, headers = headers).text
print(request)