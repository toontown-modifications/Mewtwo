from pandac.PandaModules import *
from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from direct.interval.IntervalGlobal import *
from game.toontown.battle.BattleProps import *
from game.toontown.racing import Piejectile


class PiejectileManager(DirectObject):
    pieCounter = 0

    def __init__(self):
        self.piejectileList = []

    def delete(self):
        for piejectile in self.piejectileList:
            self._PiejectileManager__removePiejectile(piejectile)

    def addPiejectile(self, sourceId, targetId=0, type=0):
        name = 'PiejectileManager Pie %s' % PiejectileManager.pieCounter
        pie = Piejectile.Piejectile(sourceId, targetId, type, name)
        self.piejectileList.append(pie)
        PiejectileManager.pieCounter += 1

    def _PiejectileManager__removePiejectile(self, piejectile):
        self.piejectileList.remove(piejectile)
        piejectile.delete()
        piejectile = None
