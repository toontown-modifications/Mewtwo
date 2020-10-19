import requests

banEndpoint = 'https://sunrisegames.tech/bans/BanAccount.php'

username = eval(input('Username: '))
reason = eval(input('Reason for Ban: '))

# Since you are in this repository.
# I trust you to not leak this.
secretKey = 'jzYEqAZkEP'

headers = {
    'User-Agent': 'Sunrise Games - ExtAgent'
}

data = {
    'username': username,
    'banReason': reason,
    'secretKey': secretKey
}

request = requests.post(banEndpoint, data, headers = headers).text
print(request)