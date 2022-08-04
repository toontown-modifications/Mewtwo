from panda3d.core import loadPrcFile, ConfigVariableString
import requests

loadPrcFile('../../config/local.prc')

def main():
    url = 'http://unite.sunrise.games:7969/jsonrpc'
    apiToken = ConfigVariableString('api-token').getValue()

    params = {}
    params['secretKey'] = apiToken
    params['action'] = 'queryObject'
    params['arguments'] = [100000000]

    # Create our payload.
    payload = {
        'method': 'action',
        'params': params,
        'jsonrpc': '2.0',
        'id': 0
    }

    response = requests.post(url, json = payload).json()
    responseData = response['result']

    for fieldName in responseData[1]:
        value = responseData[1][fieldName]

        print(f'{fieldName}:{value}')

if __name__ == '__main__':
    main()