from game.otp.speedchat.SCMenu import SCMenu
from .TTSCToontaskTerminal import TTSCToontaskTerminal
from game.otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal
from game.toontown.quest import Quests


class TTSCToontaskMenu(SCMenu):
    def __init__(self):
        SCMenu.__init__(self)
        self.accept('questsChanged', self._TTSCToontaskMenu__tasksChanged)
        self._TTSCToontaskMenu__tasksChanged()

    def destroy(self):
        SCMenu.destroy(self)

    def _TTSCToontaskMenu__tasksChanged(self):
        self.clearMenu()

        try:
            lt = base.localAvatar
        except BaseException:
            return None

        phrases = []

        def addTerminal(terminal, self=self, phrases=phrases):
            displayText = terminal.getDisplayText()
            if displayText not in phrases:
                self.append(terminal)
                phrases.append(displayText)

        for task in lt.quests:
            (taskId, fromNpcId, toNpcId, rewardId, toonProgress) = task
            q = Quests.getQuest(taskId)
            if q is None:
                continue

            msgs = q.getSCStrings(toNpcId, toonProgress)
            if not isinstance(msgs, type([])):
                msgs = [msgs]

            for i in range(len(msgs)):
                addTerminal(
                    TTSCToontaskTerminal(msgs[i], taskId, toNpcId,
                                         toonProgress, i))

        needToontask = 1
        if hasattr(lt, 'questCarryLimit'):
            needToontask = len(lt.quests) != lt.questCarryLimit

        if needToontask:
            addTerminal(SCStaticTextTerminal(1299))
