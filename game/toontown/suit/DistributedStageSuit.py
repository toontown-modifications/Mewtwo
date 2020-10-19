from game.toontown.suit import DistributedFactorySuit
from game.toontown.suit.Suit import *
from direct.directnotify import DirectNotifyGlobal
from direct.actor import Actor
from game.otp.avatar import Avatar
from . import SuitDNA
from game.toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
from game.toontown.battle import SuitBattleGlobals
from direct.task import Task
from game.toontown.battle import BattleProps
from game.toontown.toonbase import TTLocalizer
import string


class DistributedStageSuit(DistributedFactorySuit.DistributedFactorySuit):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedStageSuit')

    def setCogSpec(self, spec):
        self.spec = spec
        self.setPos(spec['pos'])
        self.setH(spec['h'])
        self.originalPos = spec['pos']
        self.escapePos = spec['pos']
        self.pathEntId = spec['path']
        self.behavior = spec['behavior']
        self.skeleton = spec['skeleton']
        self.boss = spec['boss']
        self.revives = spec.get('revives')
        if self.reserve:
            self.reparentTo(hidden)
        else:
            self.doReparent()
