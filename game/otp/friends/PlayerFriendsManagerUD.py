from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from game.otp.friends.FriendInfo import FriendInfo

class PlayerFriendsManagerUD(DistributedObjectGlobalUD):
    notify = directNotify.newCategory('PlayerFriendsManagerUD')

    def avatarOnline(self, avatarId):
        friend = FriendInfo('{0}'.format(100000003), playerName = 'Pirate', onlineYesNo = 1, avatarId = 100000003, location = 'Pirates')
        self.sendUpdateToAvatarId(avatarId, 'updatePlayerFriend', [100000003, friend, 1])

    def requestInvite(self, todo0, todo1, todo2):
        pass

    def invitationFrom(self, todo0, todo1):
        pass

    def retractInvite(self, todo0):
        pass

    def invitationResponse(self, todo0, todo1, todo2):
        pass

    def requestDecline(self, todo0, todo1):
        pass

    def requestDeclineWithReason(self, todo0, todo1, todo2):
        pass

    def requestRemove(self, todo0, todo1):
        pass

    def secretResponse(self, todo0):
        pass

    def rejectSecret(self, todo0):
        pass

    def rejectUseSecret(self, todo0):
        pass

    def updatePlayerFriend(self, todo0, todo1, todo2):
        pass

    def removePlayerFriend(self, todo0):
        pass
