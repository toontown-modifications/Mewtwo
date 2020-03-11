from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.building.DistributedDoorAI import DistributedDoorAI

class DistributedHouseDoorAI(DistributedDoorAI):
    notify = directNotify.newCategory('DistributedHouseDoorAI')