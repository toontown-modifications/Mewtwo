from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.toonbase import ToontownGlobals
from game.toontown.suit import SuitDNA

import random

class SuitInvasionManagerAI:
    notify = directNotify.newCategory('SuitInvasionManagerAI')

    def __init__(self, air):
        self.air = air

        self.invadingCog = (None, 0)
        self.numCogs = 0

        self.constantInvasionsDistrict = False

        if self.air.districtName == 'Nutty River':
            self.constantInvasionsDistrict = True
            self.invading = True
        else:
            self.invading = False

    def generateInitialInvasion(self, task = None):
        cogType = random.choice(SuitDNA.suitHeadTypes)
        numCogs = random.randint(1000, 3000)

        skeleton = 0

        self.startInvasion(cogType, numCogs, skeleton)

        if task:
            return task.done

    def setInvadingCog(self, suitName, skeleton):
        self.invadingCog = (suitName, skeleton)

    def getInvadingCog(self):
        return self.invadingCog

    def getInvading(self):
        return self.invading

    def _spGetOut(self):
        for suitPlanner in self.air.suitPlanners.values():
            suitPlanner.flySuits()

    def decrementNumCogs(self):
        self.numCogs -= 1
        if self.numCogs <= 0:
            self.stopInvasion()

    def stopInvasion(self, task = None):
        if not self.getInvading():
            return

        self.air.newsManager.d_setInvasionStatus(ToontownGlobals.SuitInvasionEnd, self.invadingCog[0], self.numCogs, self.invadingCog[1])
        if task:
            task.remove()
        else:
            taskMgr.remove('invasion-timeout')

        self.numCogs = 0

        if self.constantInvasionsDistrict:
            self.generateInitialInvasion()
        else:
            self.setInvadingCog(None, 0)
            self.invading = False
            self._spGetOut()

    def startInvasion(self, cogType, numCogs, skeleton):
        if not self.constantInvasionsDistrict and self.getInvading():
            return False

        self.numCogs = numCogs
        self.setInvadingCog(cogType, skeleton)
        self.invading = True
        self.air.newsManager.d_setInvasionStatus(ToontownGlobals.SuitInvasionBegin, self.invadingCog[0], self.numCogs, self.invadingCog[1])
        self._spGetOut()
        timePerSuit = config.GetFloat('invasion-time-per-suit', 1.2)
        taskMgr.doMethodLater(self.numCogs * timePerSuit, self.stopInvasion, 'invasion-timeout')
        return True