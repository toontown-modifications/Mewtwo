from game.toontown.ai.MessageTypes import *
from game.otp.distributed import OtpDoGlobals
from game.toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from game.toontown.toonbase import ToontownGlobals

from game.otp.distributed.DistributedDirectoryAI import DistributedDirectoryAI
from game.otp.uberdog.DistributedChatManagerUD import DistributedChatManagerUD

from game.toontown.parties.ToontownTimeManager import ToontownTimeManager

import time

class ToontownUDRepository(ToontownInternalRepository):

    def __init__(self, baseChannel, stateServerChannel):
        ToontownInternalRepository.__init__(self, baseChannel, stateServerChannel, dcSuffix = 'UD')

        self.notify.setInfo(True)

    def createGlobals(self):
        self.chatManager = DistributedChatManagerUD(self)
        self.chatManager.generateWithRequiredAndId(OtpDoGlobals.OTP_DO_ID_CHAT_MANAGER, 0, 0)

        self.partyManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER, 'DistributedPartyManager')
        self.centralLogger = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_CENTRAL_LOGGER, 'CentralLogger')

    def createLocals(self):
        self.toontownTimeManager = ToontownTimeManager(serverTimeUponLogin = int(time.time()), globalClockRealTimeUponLogin = globalClock.getRealTime())

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        # Create our root object.
        self.notify.info('Creating root object ({0})...'.format(self.getGameDoId()))
        rootObj = DistributedDirectoryAI(self)
        rootObj.generateWithRequiredAndId(self.getGameDoId(), 0, 0)     

        # Create our local objects...
        self.notify.info('Creating locals...')
        self.createLocals()

        # Create our global objects.
        self.notify.info('Creating globals...')
        self.createGlobals()

        self.notify.info('Done.')