from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.AstronInternalRepository import AstronInternalRepository
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.distributed.PyDatagram import *
from TimeManagerAI import TimeManagerAI
from DistributedDistrictAI import DistributedDistrictAI
from ToontownDistrictStatsAI import ToontownDistrictStatsAI
from server import OtpDoGlobals

class ToontownAIRepository(AstronInternalRepository):
    dbId = 4003
    GameGlobalsId = 4618
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
        self.districtId = self.allocateChannel()

        # Generate our district.
        self.district = DistributedDistrictAI(self)
        self.district.setName('Sillyville')
        self.district.generateWithRequiredAndId(self.districtId, self.getGameDoId(), OtpDoGlobals.OTP_ZONE_ID_DISTRICTS)
        self.district.setAI(self.ourChannel)

        self.districtStats = ToontownDistrictStatsAI(self)
        self.districtStats.settoontownDistrictId(self.districtId)
        self.districtStats.generateWithRequiredAndId(self.allocateChannel(), self.getGameDoId(), OtpDoGlobals.OTP_ZONE_ID_DISTRICTS_STATS)

        # Generate our TimeManagerAI.
        self.timeManager = TimeManagerAI(self)
        self.timeManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.district.b_setAvailable(1)

        # Inform the ExtAgent of us.
        self.netMessenger.send('registerShard', [self.districtId, config.GetString('air-shardname', 'District')])
