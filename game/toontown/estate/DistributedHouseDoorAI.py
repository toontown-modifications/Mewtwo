from direct.directnotify import DirectNotifyGlobal

from game.toontown.building.DistributedDoorAI import DistributedDoorAI


class DistributedHouseDoorAI(DistributedDoorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedHouseDoorAI')
