import requests

banEndpoint = 'https://sunrisegames.tech/bans/BanAccount.php'

username = input('Username: ')
reason = input('Reason for Ban: ')

# Since you are in this repository.
# I trust you to not leak this.
secretKey = 'jzYEqAZkEP'

data = {
    'username': username,
    'banReason': reason,
    'secretKey': secretKey
}

request = requests.post(banEndpoint, data).text
print(request)