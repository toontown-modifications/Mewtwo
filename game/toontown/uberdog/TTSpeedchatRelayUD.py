from direct.directnotify.DirectNotifyGlobal import directNotify
from game.otp.uberdog.SpeedchatRelayUD import SpeedchatRelayUD

class TTSpeedchatRelayUD(SpeedchatRelayUD):
    notify = directNotify.newCategory('TTSpeedchatRelayUD')