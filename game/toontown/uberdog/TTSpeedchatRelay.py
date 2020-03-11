from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.directnotify.DirectNotifyGlobal import directNotify
from game.otp.otpbase import OTPGlobals
from game.otp.uberdog.SpeedchatRelay import SpeedchatRelay
from game.otp.uberdog import SpeedchatRelayGlobals


class TTSpeedchatRelay(SpeedchatRelay):
    def __init__(self, cr):
        SpeedchatRelay.__init__(self, cr)

    def sendSpeedchatToonTask(self, receiverId, taskId, toNpcId, toonProgress,
                              msgIndex):
        self.sendSpeedchatToRelay(receiverId,
                                  SpeedchatRelayGlobals.TOONTOWN_QUEST,
                                  [taskId, toNpcId, toonProgress, msgIndex])
