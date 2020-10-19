from pandac.PandaModules import *
from . import Playground
import random

class DLPlayground(Playground.Playground):

    def __init__(self, loader, parentFSM, doneEvent):
        Playground.Playground.__init__(self, loader, parentFSM, doneEvent)

    def showPaths(self):
        from game.toontown.classicchars import CCharPaths
        from game.toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Donald))
