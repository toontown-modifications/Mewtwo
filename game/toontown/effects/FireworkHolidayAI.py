from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.toonbase import ToontownGlobals
from game.toontown.ai.HolidayBaseAI import HolidayBaseAI

import FireworkShows
from DistributedFireworkShowAI import DistributedFireworkShowAI

import time, datetime, random

class FireworkHolidayAI(HolidayBaseAI):
    notify = directNotify.newCategory('FireworkHolidayAI')

    def __init__(self, air, holidayId):
        HolidayBaseAI.__init__(self, air, holidayId)

        self.showTask = None
        self.zoneToShow = {} # zoneId: FireworkShowAI

    def start(self):
        currentMinute = self.air.toontownTimeManager.getCurServerDateTime().now(
                        tz=self.air.toontownTimeManager.serverTimeZone).minute
        if currentMinute == 0:
            # Holiday started right on top of the hour, start the show!
            self.startShow()

        self.showTask = taskMgr.doMethodLater(self.getSecondsTillHour(), self.startShow, 'hourly-fireworks')

    def stop(self):
        taskMgr.remove(self.showTask)

    def getSecondsTillHour(self):
        # Get the current epoch relative to the server's time zone.
        currentEpoch = time.mktime(datetime.datetime.now(
            tz=self.air.toontownTimeManager.serverTimeZone).timetuple()) + datetime.datetime.now(
            tz=self.air.toontownTimeManager.serverTimeZone).microsecond * 1e-6

        # The top of each hour.
        seconds = 3600.0 - (currentEpoch % 3600.0)

        return seconds

    # TODO: Create a FireworkManagerAI for the functions below
    # for starting non-holiday fireworks (magic words)

    def startShow(self, task=None):
        for hood in self.air.hoods:
            if hood.zoneId in (ToontownGlobals.SellbotHQ, ToontownGlobals.CashbotHQ, \
                                   ToontownGlobals.LawbotHQ, ToontownGlobals.BossbotHQ):
                return

            fireworkShow = DistributedFireworkShowAI(self.air, self)
            fireworkShow.generateWithRequired(hood.zoneId)

            if self.holidayId in FireworkShows.shows:
                style = random.randint(0, len(FireworkShows.shows[self.holidayId]) - 1)
            else:
                style = 0
            fireworkShow.d_startShow(self.holidayId, style)

            self.zoneToShow[hood.zoneId] = fireworkShow

        if task:
            task.delayTime = self.getSecondsTillHour()
            return task.again

    def stopShow(self, zoneId):
        fireworkShow = self.zoneToShow.get(zoneId)
        if not fireworkShow:
            # Non-existent firework show???
            return

        fireworkShow.requestDelete()

    def isShowRunning(self):
        pass