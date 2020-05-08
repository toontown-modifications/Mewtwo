from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.estate.DistributedStatuaryAI import DistributedStatuaryAI

class DistributedChangingStatuaryAI(DistributedStatuaryAI):
    notify = directNotify.newCategory('DistributedChangingStatuaryAI')
