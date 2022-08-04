from panda3d.core import loadPrcFile, ConfigVariableString
import requests, json

loadPrcFile('../../config/local.prc')

def main():
    url = 'http://127.0.0.1:7969/jsonrpc'
    secretKey = ConfigVariableString('secret-key').getValue()

    params = {}
    params['secretKey'] = secretKey
    params['action'] = 'retrieveAccountId'
    params['arguments'] = ['Rocket']

    # Create our payload.
    payload = {
        'method': 'action',
        'params': params,
        'jsonrpc': '2.0',
        'id': 0
    }

    response = requests.post(url, json = payload).json()
    print(response['result'])

if __name__ == '__main__':
    main()