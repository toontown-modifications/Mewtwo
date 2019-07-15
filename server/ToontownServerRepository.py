from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.AstronInternalRepository import AstronInternalRepository
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from ExtAgent import ExtAgent

class ToontownServerRepository(AstronInternalRepository):
    dbId = 4003

    def __init__(self):
        AstronInternalRepository.__init__(self,
                                          config.GetInt('server-base-channel', 0),
                                          config.GetInt('air-stateserver', 0),
                                          dcSuffix='UD')

    def GetPuppetConnectionChannel(self, doId):
        return doId + (1001 << 32)

    def GetAccountConnectionChannel(self, doId):
        return doId + (1003 << 32)

    def handleConnected(self):
        AstronInternalRepository.handleConnected(self)

        # Generate a DistributedObjectAI to act as a "root object".
        self.rootObject = DistributedObjectAI(self)
        self.rootObject.generateWithRequiredAndId(2, 0, 0)

        self.extAgent = ExtAgent(self)

    def handleDatagram(self, dgi):
        msgType = self.getMsgType()
        if not msgType:
            return

        if msgType == 1205:
            self.extAgent.handleDatagram(dgi)
            return
        elif msgType == 1206:
            self.extAgent.handleResp(dgi)
            return

        AstronInternalRepository.handleDatagram(self, dgi)