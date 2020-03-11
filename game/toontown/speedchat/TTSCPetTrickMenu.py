from direct.directnotify import DirectNotifyGlobal
from game.otp.speedchat.SCMenu import SCMenu
from game.otp.speedchat import SCMenuHolder
from game.otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from game.otp.otpbase import OTPLocalizer
from game.toontown.pets import PetTricks


class TTSCPetTrickMenu(SCMenu):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTSCPetTrickMenu')

    def __init__(self):
        SCMenu.__init__(self)
        self.accept('petTrickPhrasesChanged',
                    self._TTSCPetTrickMenu__phrasesChanged)
        self._TTSCPetTrickMenu__phrasesChanged()

    def destroy(self):
        self.ignore('petTrickPhrasesChanged')
        SCMenu.destroy(self)

    def _TTSCPetTrickMenu__phrasesChanged(self, zoneId=0):
        self.clearMenu()

        try:
            lt = base.localAvatar
        except BaseException:
            return None

        for trickId in lt.petTrickPhrases:
            if trickId not in PetTricks.TrickId2scIds:
                TTSCPetTrickMenu.notify.warning(
                    'unknown trick ID: %s' % trickId)
                continue
            for msg in PetTricks.TrickId2scIds[trickId]:
                self.append(SCStaticTextTerminal(msg))
