import socket, base64, json

messageRequest = {
    'whatToDo': 'systemMessage',
    'message': 'System message test from Twisted server.',
    'signature': base64.b64decode('UGxlYXNlRG9Ob3RBYnVzZVRoaXNGdW5jdGlvbg==')
}

request = json.dumps(messageRequest)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 7199))

# Send our request.
client.sendall(request)