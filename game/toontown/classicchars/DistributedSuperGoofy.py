from pandac.PandaModules import *
from . import DistributedCCharBase
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from game.toontown.classicchars import DistributedGoofySpeedway
from . import CharStateDatas
from game.toontown.toonbase import ToontownGlobals
from game.toontown.toonbase import TTLocalizer
from . import DistributedCCharBase


class DistributedSuperGoofy(DistributedGoofySpeedway.DistributedGoofySpeedway):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedSuperGoofy')

    def __init__(self, cr):

        try:
            pass
        except BaseException:
            self.DistributedGoofySpeedway_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(
                self, cr, TTLocalizer.SuperGoofy, 'sg')
            self.fsm = ClassicFSM.ClassicFSM(self.getName(), [
                State.State('Off', self.enterOff, self.exitOff, ['Neutral']),
                State.State('Neutral', self.enterNeutral, self.exitNeutral,
                            ['Walk']),
                State.State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])
            ], 'Off', 'Off')
            self.fsm.enterInitialState()
            self.nametag.setName(TTLocalizer.Goofy)

    def walkSpeed(self):
        return ToontownGlobals.SuperGoofySpeed
