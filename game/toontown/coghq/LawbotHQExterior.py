from direct.directnotify import DirectNotifyGlobal
from game.toontown.battle import BattlePlace
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from game.toontown.toonbase import ToontownGlobals
from game.toontown.building import Elevator
from pandac.PandaModules import *
from game.toontown.coghq import CogHQExterior

class LawbotHQExterior(CogHQExterior.CogHQExterior):
    notify = DirectNotifyGlobal.directNotify.newCategory('LawbotHQExterior')
