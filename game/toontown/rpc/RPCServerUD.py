from direct.directnotify.DirectNotifyGlobal import directNotify

from game.otp.distributed import OtpDoGlobals
from game.otp.otpbase import OTPLocalizer

from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from jsonrpc import JSONRPCResponseManager, dispatcher
from threading import Thread

class RPCServerUD:
    notify = directNotify.newCategory('RPCServerUD')

    def __init__(self, air):
        self.air = air

        # Start up the RPC service thread.
        Thread(target = self.startup, args = ()).start()

    @Request.application
    def application(self, request):
        # Dispatcher is dictionary {<method_name>: callable}.
        dispatcher['echo'] = lambda s: s
        dispatcher['add'] = lambda a, b: a + b
        dispatcher['action'] = self.handleAction

        response = JSONRPCResponseManager.handle(request.data, dispatcher)
        return Response(response.json, mimetype = 'application/json')

    def handleAction(self, secretKey, action, arguments):
        if secretKey != 'jzYEqAZkEP':
            return 'Nice try.'

        if action == 'systemMessage':
            message = arguments[0]
            self.sendSystemMessage(message)
            return 'Broadcasted system message to shard.'
        elif action == 'kickPlayer':
            if len(arguments) == 2:
                avId = int(arguments[0])
                reason = arguments[1]
                self.air.extAgent.sendKick(avId, reason)
                return 'Kicked player from server.'
            elif action == 'approveName':
                avId = int(arguments[0])
                self.air.extAgent.approveName(avId)
                return 'Approved name.'
            elif whatToDo == 'rejectName':
                avId = int(arguments[0])
                self.air.extAgent.rejectName(avId)
                return 'Rejected name.'

        return 'Unhandled action.'

    def sendSystemMessage(self, message):
        channels = simbase.air.extAgent.clientChannel2avId

        for clientChannel in channels:
            self.air.extAgent.sendSystemMessage(clientChannel, message)

    def startup(self):
        run_simple('0.0.0.0', 8080, self.application)