from pandac.PandaModules import *
from game.toontown.toonbase.ToontownGlobals import *
from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
from game.toontown.toontowngui import TTDialog
from game.otp.otpbase import OTPLocalizer
from game.toontown.toontowngui import ToonHeadDialog
from direct.gui.DirectGui import DGG
from game.otp.otpbase import OTPGlobals


class FriendInvitee(ToonHeadDialog.ToonHeadDialog):
    notify = DirectNotifyGlobal.directNotify.newCategory('FriendInvitee')

    def __init__(self, avId, avName, avDNA, context, **kw):
        self.avId = avId
        self.avDNA = avDNA
        self.context = context
        self.avName = avName
        if len(base.localAvatar.friendsList) >= MaxFriends:
            base.cr.friendManager.up_inviteeFriendResponse(3, self.context)
            self.context = None
            text = OTPLocalizer.FriendInviteeTooManyFriends % self.avName
            style = TTDialog.Acknowledge
            buttonTextList = [OTPLocalizer.FriendInviteeOK]
            command = self._FriendInvitee__handleOhWell
        else:
            text = OTPLocalizer.FriendInviteeInvitation % self.avName
            style = TTDialog.TwoChoice
            buttonTextList = [
                OTPLocalizer.FriendInviteeOK, OTPLocalizer.FriendInviteeNo
            ]
            command = self._FriendInvitee__handleButton
        optiondefs = (('dialogName', 'FriendInvitee',
                       None), ('text', text, None), ('style', style, None),
                      ('buttonTextList', buttonTextList,
                       None), ('command', command, None),
                      ('image_color', (1.0, 0.89000000000000001,
                                       0.77000000000000002, 1.0),
                       None), ('geom_scale', 0.20000000000000001,
                               None), ('geom_pos', (-0.10000000000000001, 0,
                                                    -0.025000000000000001),
                                       None), ('pad', (0.074999999999999997,
                                                       0.074999999999999997),
                                               None), ('topPad', 0, None),
                      ('midPad', 0, None), ('pos', (0.45000000000000001, 0,
                                                    0.75), None), ('scale',
                                                                   0.75, None))
        self.defineoptions(kw, optiondefs)
        ToonHeadDialog.ToonHeadDialog.__init__(self, self.avDNA)
        self.accept('cancelFriendInvitation',
                    self._FriendInvitee__handleCancelFromAbove)
        self.initialiseoptions(FriendInvitee)
        self.show()

    def cleanup(self):
        ToonHeadDialog.ToonHeadDialog.cleanup(self)
        self.ignore('cancelFriendInvitation')
        if self.context is not None:
            base.cr.friendManager.up_inviteeFriendResponse(2, self.context)
            self.context = None

        if base.friendMode == 1:
            base.cr.friendManager.executeGameSpecificFunction()

    def _FriendInvitee__handleButton(self, value):
        print('handleButton')
        if value == DGG.DIALOG_OK:
            if base.friendMode == 0:
                base.cr.friendManager.up_inviteeFriendResponse(1, self.context)
            elif base.friendMode == 1:
                print('sending Request Invite')
                base.cr.avatarFriendsManager.sendRequestInvite(self.avId)

        elif base.friendMode == 0:
            base.cr.friendManager.up_inviteeFriendResponse(0, self.context)
        elif base.friendMode == 1:
            base.cr.avatarFriendsManager.sendRequestRemove(self.avId)

        self.context = None
        self.cleanup()

    def _FriendInvitee__handleOhWell(self, value):
        self.cleanup()

    def _FriendInvitee__handleCancelFromAbove(self, context=None):
        if context is None or context == self.context:
            self.context = None
            self.cleanup()
