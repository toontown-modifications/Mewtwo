from direct.showbase import PythonUtil
from game.otp.speedchat.SCMenu import SCMenu
from game.otp.speedchat.SCMenuHolder import SCMenuHolder
from game.otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from game.otp.otpbase import OTPLocalizer
SillyPhaseOneMenu = [(OTPLocalizer.SillyHolidayMenuSections[1],
                      [30303, 30304, 30305, 30306]),
                     (OTPLocalizer.SillyHolidayMenuSections[2], [30307,
                                                                 30308]),
                     (OTPLocalizer.SillyHolidayMenuSections[0], [30301,
                                                                 30302])]


class TTSCSillyPhaseOneMenu(SCMenu):
    def __init__(self):
        SCMenu.__init__(self)
        self._TTSCSillyPhaseOneMenu__SillyPhaseOneMessagesChanged()
        submenus = []

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def _TTSCSillyPhaseOneMenu__SillyPhaseOneMessagesChanged(self):
        self.clearMenu()

        try:
            lt = base.localAvatar
        except BaseException:
            return None

        for section in SillyPhaseOneMenu:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print 'warning: tried to link Silly PhaseOne phrase %s which does not seem to exist' % phrase
                        break

                    self.append(SCStaticTextTerminal(phrase))

            menu = SCMenu()
            for phrase in section[1]:
                if phrase not in OTPLocalizer.SpeedChatStaticText:
                    print 'warning: tried to link Silly PhaseOne phrase %s which does not seem to exist' % phrase
                    break

                menu.append(SCStaticTextTerminal(phrase))

            menuName = str(section[0])
            self.append(SCMenuHolder(menuName, menu))
