from game.toontown.cogdominium import CogdoBoardroomGameSpec
from game.toontown.cogdominium import CogdoBoardroomGameConsts as Consts

class CogdoBoardroomGameBase:

    def getConsts(self):
        return Consts

    def getSpec(self):
        return CogdoBoardroomGameSpec
