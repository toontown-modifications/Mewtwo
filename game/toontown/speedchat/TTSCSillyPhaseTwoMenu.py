from direct.showbase import PythonUtil
from game.otp.speedchat.SCMenu import SCMenu
from game.otp.speedchat.SCMenuHolder import SCMenuHolder
from game.otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from game.otp.otpbase import OTPLocalizer
SillyPhaseTwoMenu = [(OTPLocalizer.SillyHolidayMenuSections[1],
                      [30310, 30311, 30312, 30313, 30314, 30315]),
                     (OTPLocalizer.SillyHolidayMenuSections[2], [30316,
                                                                 30317]),
                     (OTPLocalizer.SillyHolidayMenuSections[0], [30309])]


class TTSCSillyPhaseTwoMenu(SCMenu):
    def __init__(self):
        SCMenu.__init__(self)
        self._TTSCSillyPhaseTwoMenu__SillyPhaseTwoMessagesChanged()
        submenus = []

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def _TTSCSillyPhaseTwoMenu__SillyPhaseTwoMessagesChanged(self):
        self.clearMenu()

        try:
            lt = base.localAvatar
        except BaseException:
            return None

        for section in SillyPhaseTwoMenu:
            if section[0] == -1:
                for phrase in section[1]:
                    if phrase not in OTPLocalizer.SpeedChatStaticText:
                        print('warning: tried to link Silly PhaseTwo phrase %s which does not seem to exist' % phrase)
                        break

                    self.append(SCStaticTextTerminal(phrase))

            menu = SCMenu()
            for phrase in section[1]:
                if phrase not in OTPLocalizer.SpeedChatStaticText:
                    print('warning: tried to link Silly PhaseTwo phrase %s which does not seem to exist' % phrase)
                    break

                menu.append(SCStaticTextTerminal(phrase))

            menuName = str(section[0])
            self.append(SCMenuHolder(menuName, menu))
