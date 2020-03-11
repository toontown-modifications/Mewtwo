import string
import sys
from direct.showbase import DirectObject
from game.otp.otpbase import OTPLocalizer
from game.toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal
from game.otp.otpbase import OTPGlobals
from game.otp.speedchat import SCDecoders
from pandac.PandaModules import *
from game.otp.chat.ChatGlobals import *
from game.otp.chat.TalkGlobals import *
from game.otp.speedchat import SpeedChatGlobals
from game.otp.chat.TalkMessage import TalkMessage
from game.otp.chat.TalkAssistant import TalkAssistant
from game.toontown.speedchat import TTSCDecoders
import time


class TTTalkAssistant(TalkAssistant):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTTalkAssistant')

    def __init__(self):
        TalkAssistant.__init__(self)

    def clearHistory(self):
        TalkAssistant.clearHistory(self)

    def sendPlayerWhisperToonTaskSpeedChat(self, taskId, toNpcId, toonProgress,
                                           msgIndex, receiverId):
        error = None
        base.cr.speedchatRelay.sendSpeedchatToonTask(receiverId, taskId,
                                                     toNpcId, toonProgress,
                                                     msgIndex)
        message = TTSCDecoders.decodeTTSCToontaskMsg(taskId, toNpcId,
                                                     toonProgress, msgIndex)
        if self.logWhispers:
            receiverName = self.findName(receiverId, 1)
            newMessage = TalkMessage(self.countMessage(), self.stampTime(),
                                     message, localAvatar.doId,
                                     localAvatar.getName(), localAvatar.DISLid,
                                     localAvatar.DISLname, None, None,
                                     receiverId, receiverName, TALK_ACCOUNT,
                                     None)
            self.historyComplete.append(newMessage)
            self.addToHistoryDoId(newMessage, localAvatar.doId)
            self.addToHistoryDISLId(
                newMessage, base.cr.accountDetailRecord.playerAccountId)
            messenger.send('NewOpenMessage', [newMessage])

        return error

    def sendToonTaskSpeedChat(self, taskId, toNpcId, toonProgress, msgIndex):
        error = None
        messenger.send(SCChatEvent)
        messenger.send('chatUpdateSCToontask',
                       [taskId, toNpcId, toonProgress, msgIndex])
        return error
