import requests

terminateEndpoint = 'https://sunrise.games/bans/TerminateAccount.php'

username = input('Username: ')
reason = 'Violated rules multiple times.'

# Since you are in this repository.
# I trust you to not leak this.
secretKey = 'jzYEqAZkEP'

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