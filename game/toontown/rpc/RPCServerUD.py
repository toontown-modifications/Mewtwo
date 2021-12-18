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
        Thread(target = self.startup).start()

    @Request.application
    def application(self, request):
        # Dispatcher is dictionary {<method_name>: callable}.
        dispatcher['echo'] = lambda s: s
        dispatcher['add'] = lambda a, b: a + b
        dispatcher['action'] = self.handleAction

        response = JSONRPCResponseManager.handle(request.data, dispatcher)
        return Response(response.json, mimetype = 'application/json')

    def handleAction(self, secretKey, action, arguments):
        if secretKey != config.GetString('rpc-key'):
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
        elif action == 'rejectName':
            avId = int(arguments[0])
            self.air.extAgent.rejectName(avId)
            return 'Rejected name.'
        elif action == 'banPlayer':
            avatarId = int(arguments[0])

            def handleRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonUD']:
                    return

                accountId = fields['setDISLid'][0]
                playToken = self.air.extAgent.accId2playToken.get(accountId, '')

                self.air.extAgent.sendKick(avatarId, 'N/A')
                self.air.extAgent.banAccount(playToken, 'N/A', 'N/A', True)

            # Query the avatar to get some account information.
            self.air.dbInterface.queryObject(self.air.dbId, avatarId, handleRetrieve)
            return 'Banned avatar.'
        elif action == 'warnPlayer':
            avId = int(arguments[0])
            reason = str(arguments[1])

            avClientChannel = self.air.GetPuppetConnectionChannel(avId)
            self.air.extAgent.warnPlayer(avClientChannel, reason)
            return 'Warned avatar.'
        elif action == 'retrieveAccountId':
            playToken = str(arguments[0])
            accountId = self.air.extAgent.query(playToken)

            response = f'No account found associated with {playToken}!'

            if accountId:
                response = f'The accountId associated with {playToken} is {accountId}.'

            return response
        elif action == 'queryObject':
            doId = int(arguments[0])

            result = []

            def callback(dclass, fields):
                if dclass is not None:
                    dclass = dclass.getName()

                    result.extend([dclass, fields])

            self.air.dbInterface.queryObject(self.air.dbId, doId, callback)

            return result

        return 'Unhandled action.'

    def sendSystemMessage(self, message):
        channels = simbase.air.extAgent.clientChannel2avId

        for clientChannel in channels:
            self.air.extAgent.sendSystemMessage(clientChannel, message)

    def startup(self):
        run_simple('0.0.0.0', 7969, self.application)