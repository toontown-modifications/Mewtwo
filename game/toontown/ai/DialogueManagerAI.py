from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.toonbase import TTLocalizer

from game.libotp import _constants

class DialogueManagerAI:
    notify = directNotify.newCategory('DialogueManagerAI')

    def __init__(self, air):
        self.air = air

    def requestDialogue(self, npc, topic, endPause):
        npc.sendUpdate('setChat', [topic, 1, 2020, _constants.CFSpeech | _constants.CFTimeout])

    def leaveDialogue(self, _):
        pass