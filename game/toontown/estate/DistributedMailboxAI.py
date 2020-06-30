from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from game.toontown.estate import MailboxGlobals
from game.toontown.parties.PartyGlobals import InviteStatus
from game.toontown.toonbase import ToontownGlobals

class DistributedMailboxAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedMailboxAI')

    def __init__(self, air, house):
        DistributedObjectAI.__init__(self, air)

        self.house = house
        self.houseId = self.house.doId
        self.housePos = self.house.housePos
        self.name = self.house.name
        self.busy = False
        self.user = None
        self.fullIndicator = 0

    def generate(self):
        DistributedObjectAI.generate(self)

        self.updateIndicatorFlag()

    def getHouseId(self):
        return self.houseId

    def getHousePos(self):
        return self.housePos

    def getName(self):
        return self.name

    def setFullIndicator(self, fullIndicator):
        self.fullIndicator = fullIndicator

    def d_setFullIndicator(self, fullIndicator):
        self.sendUpdate('setFullIndicator', [fullIndicator])

    def b_setFullIndicator(self, fullIndicator):
        self.setFullIndicator(fullIndicator)
        self.d_setFullIndicator(fullIndicator)

    def getFullIndicator(self):
        return self.fullIndicator

    def avatarEnter(self):
        if self.busy:
            return

        avId = self.air.getAvatarIdFromSender()
        if avId != self.house.avatarId:
            self.d_setMovie(MailboxGlobals.MAILBOX_MOVIE_NOT_OWNER, avId)
            self.resetMovie()
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if len(av.mailboxContents) != 0 or av.numMailItems or av.getNumInvitesToShowInMailbox() or len(av.awardMailboxContents) != 0:
            self.d_setMovie(MailboxGlobals.MAILBOX_MOVIE_READY, avId)
            self.user = avId
            self.busy = True
        elif len(av.onOrder):
            self.d_setMovie(MailboxGlobals.MAILBOX_MOVIE_WAITING, avId)
        else:
            self.d_setMovie(MailboxGlobals.MAILBOX_MOVIE_EMPTY, avId)

        self.resetMovie()

    def avatarExit(self):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.user:
            return

        self.user = None
        self.busy = False
        self.updateIndicatorFlag()
        self.d_setMovie(MailboxGlobals.MAILBOX_MOVIE_EXIT, avId)
        self.d_freeAvatar(avId)
        self.resetMovie()

    def d_freeAvatar(self, avId):
        self.sendUpdateToAvatarId(avId, 'freeAvatar', [])

    def d_setMovie(self, movie, avId):
        self.sendUpdate('setMovie', [movie, avId])

    def acceptItemMessage(self, context, item, index, optional):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.user:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if index >= len(av.mailboxContents):
            self.sendUpdateToAvatarId(avId, 'acceptItemResponse', [context, ToontownGlobals.P_InvalidIndex])
            return

        item = av.mailboxContents[index]
        del av.mailboxContents[index]
        av.b_setMailboxContents(av.mailboxContents)
        self.sendUpdateToAvatarId(avId, 'acceptItemResponse', [context, item.recordPurchase(av, optional)])

    def discardItemMessage(self, context, item, index, optional):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.user:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if index >= len(av.mailboxContents):
            self.sendUpdateToAvatarId(avId, 'discardItemResponse', [context, ToontownGlobals.P_InvalidIndex])
            return

        del av.mailboxContents[index]
        av.b_setMailboxContents(av.mailboxContents)
        self.sendUpdateToAvatarId(avId, 'discardItemResponse', [context, ToontownGlobals.P_ItemAvailable])

    def acceptInviteMessage(self, context, inviteKey):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.user:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        av.updateInvite(inviteKey, InviteStatus.Accepted)
        av.sendUpdate('setInvites', [av.invites[:]])
        self.air.partyManager.sendRespondToInvite(avId, 0, 0, inviteKey, InviteStatus.Accepted)
        self.sendUpdateToAvatarId(avId, 'acceptItemResponse', [context, ToontownGlobals.P_ItemAvailable])

    def rejectInviteMessage(self, context, inviteKey):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.user:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        av.updateInvite(inviteKey, InviteStatus.Rejected)
        av.sendUpdate('setInvites', [av.invites[:]])
        self.air.partyManager.sendRespondToInvite(avId, 0, 0, inviteKey, InviteStatus.Rejected)
        self.sendUpdateToAvatarId(avId, 'discardItemResponse', [context, ToontownGlobals.P_ItemAvailable])

    def markInviteReadButNotReplied(self, inviteKey):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.user:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        av.updateInvite(inviteKey, InviteStatus.ReadButNotReplied)
        av.sendUpdate('setInvites', [av.invites[:]])
        self.air.partyManager.sendMarkInviteAsReadButNotReplied(avId, inviteKey)

    def updateIndicatorFlag(self):
        av = self.air.doId2do.get(self.house.avatarId)
        if av:
            self.b_setFullIndicator(len(av.mailboxContents) != 0 or av.numMailItems or av.getNumInvitesToShowInMailbox() or len(av.awardMailboxContents) != 0)
        else:
            self.b_setFullIndicator(0)

    def resetMovie(self):
        taskMgr.doMethodLater(2, self.d_setMovie, 'resetMovie-%d' % self.doId,
                              extraArgs=[MailboxGlobals.MAILBOX_MOVIE_CLEAR, 0])
