from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectUD import DistributedObjectUD
from direct.showbase import PythonUtil
from ExtAgent import ExtAgent
from game.otp.distributed.DistributedDirectoryAI import DistributedDirectoryAI
from game.otp.uberdog.DistributedChatManagerUD import DistributedChatManagerUD
from game.toontown.parties.ToontownTimeManager import ToontownTimeManager
from game.otp.distributed import OtpDoGlobals
from game.toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
import __builtin__, time

__builtin__.isClient = lambda: PythonUtil.isClient()

class ToontownServerRepositoryAgent(ToontownInternalRepository):

    def __init__(self):
        ToontownInternalRepository.__init__(self,
                                          config.GetInt('server-base-channel', 0),
                                          config.GetInt('air-stateserver', 0),
                                          dcSuffix='UD')

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        rootObj = DistributedDirectoryAI(self)
        rootObj.generateWithRequiredAndId(self.getGameDoId(), 0, 0)

        self.centralLogger = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_CENTRAL_LOGGER, 'CentralLogger')

        self.chatManager = DistributedChatManagerUD(self)
        self.chatManager.generateWithRequiredAndId(OtpDoGlobals.OTP_DO_ID_CHAT_MANAGER, 0, 0)

        self.toontownTimeManager = ToontownTimeManager(serverTimeUponLogin = int(time.time()), globalClockRealTimeUponLogin = globalClock.getRealTime())

        self.partyManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER, 'DistributedPartyManager')
