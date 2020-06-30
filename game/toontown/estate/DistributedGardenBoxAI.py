from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.estate.DistributedLawnDecorAI import DistributedLawnDecorAI

import GardenGlobals

class DistributedGardenBoxAI(DistributedLawnDecorAI):
    notify = directNotify.newCategory('DistributedGardenBoxAI')

    def __init__(self, mgr):
        DistributedLawnDecorAI.__init__(self, mgr)

        self.typeIndex = 0

    def announceGenerate(self):
        DistributedLawnDecorAI.announceGenerate(self)

        self.loadBox()

    def loadBox(self):
        collNode = '**/collision'

        if self.typeIndex == GardenGlobals.BOX_THREE:
            model = 'phase_5.5/models/estate/planterA'
        elif self.typeIndex == GardenGlobals.BOX_TWO:
            model = 'phase_5.5/models/estate/planterC'
        else:
            model = 'phase_5.5/models/estate/planterD'
            collNode = '**/collision2'

        render = self.getRender()

        box = loader.loadModel(model).find(collNode)

        box.setPos(self.getPos())
        box.setH(self.getH())

        box.reparentTo(render)

    def setTypeIndex(self, index):
        self.typeIndex = index

    def getTypeIndex(self):
        return self.typeIndex
