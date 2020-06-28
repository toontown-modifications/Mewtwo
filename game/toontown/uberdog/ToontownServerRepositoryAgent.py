from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectUD import DistributedObjectUD
from direct.showbase import PythonUtil
from ExtAgent import ExtAgent
from game.otp.distributed.DistributedDirectoryAI import DistributedDirectoryAI
from game.otp.uberdog.DistributedChatManagerUD import DistributedChatManagerUD
from game.toontown.parties.ToontownTimeManager import ToontownTimeManager
from game.otp.distributed import OtpDoGlobals
from game.toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from game.toontown.discord.DiscordIntegrationServer import DiscordIntegrationServer
import __builtin__, time

__builtin__.isClient = lambda: PythonUtil.isClient()

class ToontownServerRepositoryAgent(ToontownInternalRepository):
    notify = directNotify.newCategory('ToontownServerRepositoryAgent')

    def __init__(self):
        ToontownInternalRepository.__init__(self,
                                          config.GetInt('server-base-channel', 0),
                                          config.GetInt('air-stateserver', 0),
                                          dcSuffix = 'UD')

        # Enable logging.
        self.notify.setInfo(True)

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        self.notify.info('Creating root object...')
        self.createRootObject()

        self.notify.info('Creating locals...')
        self.createLocals()

        self.notify.info('Generating managers...')
        self.generateManagers()

        self.notify.info('UberDOG is now ready.')

    def createRootObject(self):
        rootObj = DistributedDirectoryAI(self)
        rootObj.generateWithRequiredAndId(self.getGameDoId(), 0, 0)

    def createLocals(self):
        if config.GetBool('want-discord-integration', False):
            self.discordIntegration = DiscordIntegrationServer(self)

        self.toontownTimeManager = ToontownTimeManager(serverTimeUponLogin = int(time.time()), globalClockRealTimeUponLogin = globalClock.getRealTime())

    def generateManagers(self):
        self.centralLogger = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_CENTRAL_LOGGER, 'CentralLogger')

        self.chatManager = DistributedChatManagerUD(self)
        self.chatManager.generateWithRequiredAndId(OtpDoGlobals.OTP_DO_ID_CHAT_MANAGER, 0, 0)

        self.partyManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER, 'DistributedPartyManager')
        self.dataStoreManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_TEMP_STORE_MANAGER, 'DistributedDataStoreManager')
        self.deliveryManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER, 'DistributedDeliveryManager')