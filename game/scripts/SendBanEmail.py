import requests

banEndpoint = 'https://sunrise.games/bans/ChatBanEmail.php'

playToken = input('Playtoken: ')
chatMessages = input('Chat messages: ')

# Since you are in this repository.
# I trust you to not leak this.
secretKey = 'jzYEqAZkEP'

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