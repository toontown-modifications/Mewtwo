from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.toonbase import ToontownGlobals
from game.toontown.discord.Webhook import Webhook
from game.toontown.uberdog.ExtAgent import ServerGlobals

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

        if self.air.isProdServer():
            # Send our invasion to the Discord channel.
            self.sendInitialInvasion()
            self.sendToServer('setInvasion')
            taskMgr.doMethodLater(30, self.sendToServer, 'Update Invasion', extraArgs = ['updateInvasion'])

        if task:
            return task.done

    def updateDiscord(self, task = None):
        fields = [{
            'name': 'Cog Type',
            'value': self.cogType,
            'inline': True
        },
        {
            'name': 'Cog Amount',
            'value': self.numCogs,
            'inline': True
        },
        {
            'name': 'District',
            'value': self.air.districtName,
            'inline': True
        }]

        message = Webhook()
        message.setDescription('A new invasion has started!')
        message.setFields(fields)
        message.setColor(14177041)
        message.setWebhook(self.webhookUrl)
        message.finalize()

        if task:
            return task.again

    def sendToServer(self, actionType = 'updateInvasion'):
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
            requests.post('https://api.sunrise.games/api/{0}'.format(actionType), json = data, headers = headers)
        except:
            self.notify.warning('Failed to send to server!')

    def getCogType(self, cogType):
        if cogType == 'f':
            return 'Flunky'
        elif cogType == 'cc':
            return 'Cold Caller'
        elif cogType == 'nd':
            return 'Name Dropper'
        elif cogType == 'b':
            return 'Bloodsucker'
        elif cogType == 'sc':
            return 'Short Change'
        elif cogType == 'pp':
            return 'Penny Pincher'
        elif cogType == 'bf':
            return 'Bottom Feeder'
        elif cogType == 'p':
            return 'Pencil Pusher'

        return cogType

    def sendInitialInvasion(self):
        fields = [{
            'name': 'Cog Type',
            'value': self.cogType,
            'inline': True
        },
        {
            'name': 'Cog Amount',
            'value': self.numCogs,
            'inline': True
        },
        {
            'name': 'District',
            'value': self.air.districtName,
            'inline': True
        }]

        message = Webhook()
        message.setDescription('A new invasion has started!')
        message.setFields(fields)
        message.setColor(14177041)
        message.setWebhook(self.webhookUrl)
        message.finalize()

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