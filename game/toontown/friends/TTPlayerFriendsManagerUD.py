from direct.directnotify import DirectNotifyGlobal
from game.otp.friends.PlayerFriendsManagerUD import PlayerFriendsManagerUD


class TTPlayerFriendsManagerUD(PlayerFriendsManagerUD):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "TTPlayerFriendsManagerUD")
