from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.safezone.DistributedSZTreasureAI import DistributedSZTreasureAI

class DistributedETreasureAI(DistributedSZTreasureAI):
    notify = directNotify.newCategory('DistributedETreasureAI')
