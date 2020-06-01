from panda3d.core import LPoint3f

from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.suit.DistributedSuitBaseAI import DistributedSuitBaseAI
from game.toontown.suit.SuitDNA import SuitDNA
from game.toontown.tutorial.DistributedBattleTutorialAI import DistributedBattleTutorialAI

class TutorialBattleManager:
    notify = directNotify.newCategory('TutorialBattleManager')

    def __init__(self, avId):
        self.avId = avId

    def destroy(self, battle):
        if battle.suitsKilledThisBattle:
            if self.avId in simbase.air.tutorialManager.playerDict.keys():
                simbase.air.tutorialManager.playerDict[self.avId].demand('HQ')

        battle.requestDelete()

class DistributedTutorialSuitAI(DistributedSuitBaseAI):
    notify = directNotify.newCategory('DistributedTutorialSuitAI')

    def __init__(self, air):
        DistributedSuitBaseAI.__init__(self, air, None)

        suitDNA = SuitDNA()
        suitDNA.newSuit('f')
        self.dna = suitDNA
        self.setLevel(1)
        self.confrontPosHpr = (0, 0, 0, 0, 0, 0)

    def destroy(self):
        del self.dna

    def requestBattle(self, x, y, z, h, p, r):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        self.confrontPosHpr = (LPoint3f(x, y, z), LPoint3f(h, p, r))
        battle = DistributedBattleTutorialAI(self.air, TutorialBattleManager(avId), LPoint3f(x, y, z), self, avId, 20001, maxSuits = 1, tutorialFlag = 1)
        battle.generateWithRequired(self.zoneId)
        battle.battleCellId = 0

    def getConfrontPosHpr(self):
        return self.confrontPosHpr