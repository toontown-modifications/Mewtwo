from direct.directnotify import DirectNotifyGlobal
from game.toontown.safezone.DistributedTreasureAI import DistributedTreasureAI


class DistributedETreasureAI(DistributedTreasureAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedETreasureAI")
