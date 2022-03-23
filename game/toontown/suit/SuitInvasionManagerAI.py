from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.toonbase import ToontownGlobals
from game.toontown.uberdog.ExtAgent import ServerGlobals
from game.toontown.battle import SuitBattleGlobals

import random, requests

class SuitInvasionManagerAI:
    notify = directNotify.newCategory('SuitInvasionManagerAI')

    def __init__(self, air):
        self.air = air

        self.invadingCog = (None, 0)
        self.numCogs = 0
        self.cogType = ''

        self.constantInvasionsDistrict = False

        self.queuedSuits = []

        if self.air.districtName == 'Nutty River':
            self.constantInvasionsDistrict = True
            self.invading = True
            self.webhookUrl = config.GetString('discord-invasions-webhook')
        else:
            self.invading = False

    def generateInitialInvasion(self, task = None):
        suitTypes = [
            'f', # Flunky
            'cc', # Cold Caller
            'nd', # Name Dropper
            'b', # Bloodsuckers
            'sc', # Short Change
            'pp', # Penny Pincher
            'bf', # Bottom Feeder
            'p' # Pencil Pusher
        ]

        if self.queuedSuits:
            cogType = self.queuedSuits[0]
            del self.queuedSuits[0]
        else:
            cogType = random.choice(suitTypes)
        numCogs = random.randint(1000, 3000)

        skeleton = 0

        self.startInvasion(cogType, numCogs, skeleton)

        if task:
            return task.done

    def sendToAPI(self, actionType = 'updateInvasion'):
        data = {
            'token': config.GetString('api-token', ''),
            'serverType': ServerGlobals.serverToName[ServerGlobals.FINAL_TOONTOWN],
            'districtName': self.air.districtName,
            'cogType': self.cogType,
            'numCogs': self.numCogs
        }

        headers = {
            'User-Agent': 'Sunrise Games - SuitInvasionManagerAI'
        }

        try:
            req = requests.post(f'https://api.sunrise.games/api/{actionType}', json = data, headers = headers)
            self.notify.info(f'Got response of {req.text} from API.')
        except:
            self.notify.warning('Failed to send to server!')

    def getCogType(self, cogType):
        return SuitBattleGlobals.SuitAttributes.get(cogType)['name']

    def setInvadingCog(self, suitName, skeleton):
        self.invadingCog = (suitName, skeleton)

    def getInvadingCog(self):
        return self.invadingCog

    def getInvading(self):
        return self.invading

    def _spGetOut(self):
        for suitPlanner in list(self.air.suitPlanners.values()):
            suitPlanner.flySuits()

    def decrementNumCogs(self):
        self.numCogs -= 1
        if self.numCogs <= 0:
            self.stopInvasion()

    def stopInvasion(self, task = None):
        if not self.getInvading():
            return

        if self.air.isProdServer():
            # Remove our invasion from the API.
            self.sendToAPI('removeInvasion')

        self.air.newsManager.d_setInvasionStatus(ToontownGlobals.SuitInvasionEnd, self.invadingCog[0], self.numCogs, self.invadingCog[1])
        if task:
            task.remove()
        else:
            taskMgr.remove('invasion-timeout')

        self.numCogs = 0
        self.cogType = ''

        if self.constantInvasionsDistrict:
            self.generateInitialInvasion()
        else:
            self.setInvadingCog(None, 0)
            self.invading = False
            self._spGetOut()

    def startInvasion(self, cogType, numCogs, skeleton):
        if not self.constantInvasionsDistrict and self.getInvading():
            return False

        if self.air.isProdServer():
            # Setup our invasion for the API.
            self.sendToAPI('setInvasion')
            taskMgr.doMethodLater(30, self.sendToAPI, 'Update Invasion', extraArgs = ['updateInvasion'])

        self.numCogs = numCogs
        self.cogType = self.getCogType(cogType)
        self.setInvadingCog(cogType, skeleton)
        self.invading = True
        self.air.newsManager.d_setInvasionStatus(ToontownGlobals.SuitInvasionBegin, self.invadingCog[0], self.numCogs, self.invadingCog[1])
        self._spGetOut()
        timePerSuit = config.GetFloat('invasion-time-per-suit', 1.2)
        taskMgr.doMethodLater(self.numCogs * timePerSuit, self.stopInvasion, 'invasion-timeout')
        return True

    def queueInvasion(self, cogType):
        self.queuedSuits.append(cogType)