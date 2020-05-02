from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedBankMgrAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedBankMgrAI')

    def transferMoney(self, amount):
        pass
