from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.AstronInternalRepository import AstronInternalRepository
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.distributed.PyDatagram import *
from game.otp.ai.TimeManagerAI import TimeManagerAI
from game.otp.distributed.DistributedDistrictAI import DistributedDistrictAI
from game.toontown.distributed.ToontownDistrictStatsAI import ToontownDistrictStatsAI
from game.toontown.ai.HolidayManagerAI import HolidayManagerAI
from game.toontown.toonbase import ToontownGlobals
from direct.showbase import PythonUtil
from server import OtpDoGlobals
import __builtin__

__builtin__.isClient = lambda: PythonUtil.isClient()

class ToontownAIRepository(AstronInternalRepository):
    dbId = 4003
    GameGlobalsId = 4618
    QuietZone = 1

    def __init__(self):
        AstronInternalRepository.__init__(self, config.GetInt('air-base-channel', 0), config.GetInt('air-stateserver', 0), dcSuffix = 'AI')

        self.districtPopulation = 0

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

    def getTrackClsends(self):
        if config.GetBool('want-track-clsends', False):
            return True

        return False

    def doLiveUpdates(self):
        if config.GetBool('want-do-live-updates', False):
            return True

        return False

    def incrementPopulation(self):
        self.districtPopulation += 1
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() + 1)

    def decrementPopulation(self):
        self.districtPopulation -= 1
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() - 1)

    def sendQueryToonMaxHp(self, doId, checkResult):
        self.notify.info('sendQueryToonMaxHp ({0}, {1})'.format(doId, checkResult))

    def _isValidPlayerLocation(self, parentId, zoneId):
        if not parentId or zoneId > ToontownGlobals.DynamicZonesEnd or zoneId is 0:
            return False

        return True

    def getAvatarExitEvent(self, doId):
        return 'distObjDelete-{0}'.format(doId)

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

        self.centralLogger = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_CENTRAL_LOGGER, 'CentralLogger')

        self.holidayManager = HolidayManagerAI(self)

        self.district.b_setAvailable(1)

        # Inform the ExtAgent of us.
        self.netMessenger.send('registerShard', [self.districtId, config.GetString('air-shardname', 'District')])
