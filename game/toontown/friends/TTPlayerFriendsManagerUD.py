from direct.directnotify.DirectNotifyGlobal import directNotify
from game.otp.friends.PlayerFriendsManagerUD import PlayerFriendsManagerUD

class TTPlayerFriendsManagerUD(PlayerFriendsManagerUD):
    notify = directNotify.newCategory('TTPlayerFriendsManagerUD')