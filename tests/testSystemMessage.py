from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory

import base64, json

class Main(Protocol):
    def connectionMade(self):
        kickRequest = {
            'whatToDo': 'systemMessage',
            'message': 'System message test from Twisted server.',
            'signature': base64.b64decode('UGxlYXNlRG9Ob3RBYnVzZVRoaXNGdW5jdGlvbg==')
        }

        request = json.dumps(kickRequest)

        self.transport.write(request)

class MainFactory(ClientFactory):
    def buildProtocol(self, addr):
        print('Connected!')
        return Main()

    def clientConnectionLost(self, connector, reason):
        print('Connection lost!')

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed!')

reactor.connectTCP('127.0.0.1', 7199, MainFactory())
reactor.run()