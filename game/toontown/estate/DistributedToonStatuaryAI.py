from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.estate.DistributedStatuaryAI import DistributedStatuaryAI

class DistributedToonStatuaryAI(DistributedStatuaryAI):
    notify = directNotify.newCategory('DistributedToonStatuaryAI')