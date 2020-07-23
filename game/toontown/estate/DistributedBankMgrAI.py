from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedBankMgrAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedBankMgrAI')

    def transferMoney(self, amount):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        av = self.air.doId2do.get(avId)

        if not av:
            return

        transactionAmount = amount

        jarMoney = av.getMoney()
        maxJarMoney = av.getMaxMoney()
        bankMoney = av.getBankMoney()
        maxBankMoney = av.getMaxBankMoney()

        transactionAmount = min(transactionAmount, jarMoney)
        transactionAmount = min(transactionAmount, maxBankMoney - bankMoney)
        transactionAmount = -min(-transactionAmount, maxJarMoney - jarMoney)
        transactionAmount = -min(-transactionAmount, bankMoney)

        newJarMoney = jarMoney - transactionAmount
        newBankMoney = bankMoney + transactionAmount

        if newJarMoney > maxJarMoney:
            return

        if newBankMoney > maxBankMoney:
            return

        av.b_setMoney(newJarMoney)
        av.b_setBankMoney(newBankMoney)