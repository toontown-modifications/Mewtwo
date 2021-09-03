from panda3d.core import loadPrcFile
import requests

# Load our configuration.
loadPrcFile('../../config/local.prc')

banEndpoint = 'https://toontastic.sunrise.games/bans/ChatBanEmail.php'

playToken = eval(input('Playtoken: '))
chatMessages = eval(input('Chat messages: '))

# If you truly need this key, ask Rocket.
secretKey = config.GetString('rpc-key')

headers = {
    'User-Agent': 'Sunrise Games - SendBanEmail'
}

data = {
    'playToken': playToken,
    'chatMessages': chatMessages,
    'secretKey': secretKey
}

request = requests.post(banEndpoint, data, headers = headers).text
print(request)