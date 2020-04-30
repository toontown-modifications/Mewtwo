from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.AstronInternalRepository import AstronInternalRepository
from direct.distributed.DistributedObjectUD import DistributedObjectUD
from direct.showbase import PythonUtil
from game.otp.distributed.DistributedDirectoryAI import DistributedDirectoryAI
from game.otp.uberdog.DistributedChatManagerUD import DistributedChatManagerUD
from game.toontown.parties.ToontownTimeManager import ToontownTimeManager
from game.otp.distributed import OtpDoGlobals
import __builtin__, time

__builtin__.isClient = lambda: PythonUtil.isClient()

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

    def GetAccountIDFromChannelCode(self, channel):
        return channel >> 32

    def GetAvatarIDFromChannelCode(self, channel):
        return channel & 0xffffffff

    def handleConnected(self):
        AstronInternalRepository.handleConnected(self)

        rootObj = DistributedDirectoryAI(self)
        rootObj.generateWithRequiredAndId(self.getGameDoId(), 0, 0)

        self.centralLogger = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_CENTRAL_LOGGER, 'CentralLogger')

        self.chatManager = DistributedChatManagerUD(self)
        self.chatManager.generateWithRequiredAndId(OtpDoGlobals.OTP_DO_ID_CHAT_MANAGER, 0, 0)

        self.toontownTimeManager = ToontownTimeManager(serverTimeUponLogin = int(time.time()), globalClockRealTimeUponLogin = globalClock.getRealTime())

        self.partyManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER, 'DistributedPartyManager')
        self.dataStoreManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_TEMP_STORE_MANAGER, 'DistributedDataStoreManager')

        if config.GetBool('want-delivery-manager', False):
            self.deliveryManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER, 'DistributedDeliveryManager')
