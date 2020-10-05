from panda3d.core import loadPrcFile
from direct.showbase import DConfig
import socket, json

loadPrcFile('../config/Config.prc')

messageRequest = {
    'whatToDo': 'systemMessage',
    'message': 'System message test from Twisted server.',
    'signature': DConfig.GetString('discord-integration-sig')
}

request = json.dumps(messageRequest)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 7199))

# Send our request.
client.sendall(request)