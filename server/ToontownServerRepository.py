from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.AstronInternalRepository import AstronInternalRepository
from direct.distributed.DistributedObjectUD import DistributedObjectUD
from ExtAgent import ExtAgent
from DistributedDirectoryAI import DistributedDirectoryAI
import OtpDoGlobals

class ToontownServerRepository(AstronInternalRepository):
    dbId = 4003
    GameGlobalsId = OtpDoGlobals.OTP_DO_ID_TOONTOWN

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

        rootObj = DistributedDirectoryAI(self)
        rootObj.generateWithRequiredAndId(self.getGameDoId(), 0, 0)

        self.centralLogger = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_CENTRAL_LOGGER, 'CentralLogger')

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