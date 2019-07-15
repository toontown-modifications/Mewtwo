from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.AstronInternalRepository import AstronInternalRepository
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.distributed.PyDatagram import *
from TimeManagerAI import TimeManagerAI

class ToontownAIRepository(AstronInternalRepository):
    dbId = 4003
    GameGlobalsId = 2
    QuietZone = 1

    def __init__(self):
        AstronInternalRepository.__init__(self,
                                          config.GetInt('air-base-channel', 0),
                                          config.GetInt('air-stateserver', 0),
                                          dcSuffix='AI')

    def getAvatarIdFromSender(self):
        return self.getMsgSender() & 0xFFFFFFFF

    def getAccountIdFromSender(self):
        return (self.getMsgSender() >> 32) & 0xFFFFFFFF

    def GetPuppetConnectionChannel(self, doId):
        return doId + (1001 << 32)

    def GetAccountConnectionChannel(self, doId):
        return doId + (1003 << 32)

    def GetAccountIDFromChannelCode(self, channel):
        return channel >> 32

    def GetAvatarIDFromChannelCode(self, channel):
        return channel & 0xffffffff

    def handleConnected(self):
        AstronInternalRepository.handleConnected(self)

        self.netMessenger.register(0, 'registerShard')

        self.createObjects()

    def createObjects(self):
        # Generate an object to act as a District.
        self.districtId = self.allocateChannel()
        self.district = DistributedObjectAI(self)
        self.district.generateWithRequiredAndId(self.districtId,
                                                self.getGameDoId(),
                                                3)

        # Claim ownership of the District.
        dg = PyDatagram()
        dg.addServerHeader(self.districtId, self.ourChannel, STATESERVER_OBJECT_SET_AI)
        dg.addChannel(self.ourChannel)
        self.send(dg)

        # Generate our TimeManagerAI.
        self.timeManager = TimeManagerAI(self)
        self.timeManager.generateWithRequired(self.QuietZone)

        # Inform the ExtAgent of us.
        self.netMessenger.send('registerShard', [self.districtId, config.GetString('air-shardname', 'District')])