from game.toontown.cogdominium import CogdoCraneGameSpec
from game.toontown.cogdominium import CogdoCraneGameConsts as Consts

class CogdoCraneGameBase:

    def getConsts(self):
        return Consts

    def getSpec(self):
        return CogdoCraneGameSpec
