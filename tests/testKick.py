import socket, base64, json

kickRequest = {
    'whatToDo': 'kickRequest',
    'reason': 'You are a pathetic skid.',
    'avId': 100000004,
    'signature': base64.b64decode('UGxlYXNlRG9Ob3RBYnVzZVRoaXNGdW5jdGlvbg==')
}

request = json.dumps(kickRequest)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 7199))

# Send our request.
client.sendall(request)