from direct.directnotify import DirectNotifyGlobal
from game.toontown.battle import SuitBattleGlobals
import random
import requests
from direct.task import Task
from game.toontown.uberdog.ExtAgent import ServerGlobals

class SuitInvasionManagerAI:
    """
    Manages invasions of Suits
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('SuitInvasionManagerAI')

    def __init__(self, air):
        self.air = air
        self.invading = 0
        self.cogType = None
        self.cogName = ""
        self.skeleton = 0
        self.totalNumCogs = 0
        self.numCogsRemaining = 0

        # Set of cog types to choose from See
        # SuitBattleGlobals.SuitAttributes.keys() for all choices I did not
        # put the highest level Cogs from each track in here to keep them
        # special and only found in buildings. I threw in the Flunky just
        # for fun.
        self.invadingCogTypes = (
            # Corporate
            'f', # Flunky
            'hh', # Head Hunter
            'cr', # Corporate Raider
            # Sales
            'tf', # Two-faced
            'm', # Mingler
            # Money
            'mb', # Money Bags
            'ls', # Loan shark
            # Legal
            'sd', # Spin Doctor
            'le', # Legal Eagle
            )

        # Picked from randomly how many cogs will invade
        # This might need to be adjusted based on population(?)
        self.invadingNumList = (1000, 2000, 3000, 4000)

        # Minimum time between invasions on this shard (in seconds)
        # No more than 1 per 2 days
        self.invasionMinDelay = 2 * 24 * 60 * 60
        # Maximum time between invasions on this shard (in seconds)
        # At least once every 7 days
        self.invasionMaxDelay = 7 * 24 * 60 * 60

        # Kick off the first invasion
        self.waitForNextInvasion()

    def sendToAPI(self, actionType="updateInvasion"):
        data = {
            "token": config.GetString("api-token", ""),
            "serverType": ServerGlobals.serverToName[ServerGlobals.FINAL_TOONTOWN],
            "districtName": self.air.districtName,
            "cogType": self.cogName,
            "numCogs": self.numCogsRemaining
        }

        headers = {
            "User-Agent": "Sunrise Games - SuitInvasionManagerAI"
        }

        try:
            req = requests.post(f"https://api.sunrise.games/api/{actionType}", json=data, headers=headers)
        except:
            self.notify.warning("Failed to send to server!")

    def getCogName(self, cogType):
        return SuitBattleGlobals.SuitAttributes.get(cogType)["name"]

    def delete(self):
        taskMgr.remove(self.taskName("cogInvasionMgr"))

    def computeInvasionDelay(self):
        # Compute the delay until the next invasion
        return ((self.invasionMaxDelay - self.invasionMinDelay) * random.random()
                + self.invasionMinDelay)

    def tryInvasionAndWaitForNext(self, task):
        # Start the invasion if there is not one already
        if self.getInvading():
            self.notify.warning("invasionTask: tried to start random invasion, but one is in progress")
        else:
            self.notify.info("invasionTask: starting random invasion")
            cogType = random.choice(self.invadingCogTypes)
            totalNumCogs = random.choice(self.invadingNumList)
            self.startInvasion(cogType, totalNumCogs)
        # In either case, fire off the next invasion
        self.waitForNextInvasion()
        return Task.done

    def waitForNextInvasion(self):
        taskMgr.remove(self.taskName("cogInvasionMgr"))
        delay = self.computeInvasionDelay()
        self.notify.info("invasionTask: waiting %s seconds until next invasion" % delay)
        taskMgr.doMethodLater(delay, self.tryInvasionAndWaitForNext,
                              self.taskName("cogInvasionMgr"))

    def getInvading(self):
        return self.invading

    def getCogType(self):
        return self.cogType, self.isSkeleton

    def getNumCogsRemaining(self):
        return self.numCogsRemaining

    def getTotalNumCogs(self):
        return self.totalNumCogs

    def startInvasion(self, cogType, totalNumCogs, skeleton=0):
        if self.invading:
            self.notify.warning("startInvasion: already invading cogType: %s numCogsRemaining: %s" %
                                (cogType, self.numCogsRemaining))
            return 0
        if not SuitBattleGlobals.SuitAttributes.get(cogType):
            self.notify.warning("startInvasion: unknown cogType: %s" % cogType)
            return 0

        self.notify.info("startInvasion: cogType: %s totalNumCogs: %s skeleton: %s" %
                          (cogType, totalNumCogs, skeleton))
        self.invading = 1
        self.cogType = cogType
        self.isSkeleton = skeleton
        self.totalNumCogs = totalNumCogs
        self.numCogsRemaining = self.totalNumCogs
        self.cogName = self.getCogName(cogType)

        # Tell the news manager that an invasion is beginning
        self.air.newsManager.invasionBegin(self.cogType, self.totalNumCogs, self.isSkeleton)

        # Get rid of all the current cogs on the streets
        # (except those already in battle, they can stay)
        for suitPlanner in self.air.suitPlanners.values():
            suitPlanner.flySuits()

        if self.air.isProdServer():
            # Setup our invasion for the API.
            self.sendToAPI("setInvasion")

        # Success!
        return 1

    def getInvadingCog(self):
        if self.invading:
            self.numCogsRemaining -= 1
            if self.numCogsRemaining <= 0:
                self.stopInvasion()
            self.notify.debug("getInvadingCog: returned cog: %s, num remaining: %s" %
                              (self.cogType, self.numCogsRemaining))
            return self.cogType, self.isSkeleton
        else:
            self.notify.debug("getInvadingCog: not currently invading")
            return None, None

    def stopInvasion(self):
        self.notify.info("stopInvasion: invasion is over now")
        # Tell the news manager that an invasion is ending
        self.air.newsManager.invasionEnd(self.cogType, 0, self.isSkeleton)
        self.invading = 0
        self.cogType = None
        self.isSkeleton = 0
        self.totalNumCogs = 0
        self.numCogsRemaining = 0
        self.cogName = ""
        # Get rid of all the current invasion cogs on the streets
        # (except those already in battle, they can stay)
        for suitPlanner in self.air.suitPlanners.values():
            suitPlanner.flySuits()

        if self.air.isProdServer():
            # Remove our invasion from the API.
            self.sendToAPI("removeInvasion")

    # Need this here since this is not a distributed object
    def taskName(self, taskString):
        return (taskString + "-" + str(hash(self)))
