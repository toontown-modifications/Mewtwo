from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.task.Task import Task
from pandac.PandaModules import *
from game.otp.avatar import DistributedAvatar
from game.toontown.toonbase.ToonBaseGlobal import *
from game.toontown.toonbase.ToontownGlobals import *
from game.toontown.distributed.ToontownMsgTypes import *
from game.toontown.minigame import Purchase
from game.toontown.parties import PartyLoader
from game.toontown.parties import PartyGlobals
from game.toontown.hood import SkyUtil
from game.toontown.hood import Hood
from game.toontown.hood import ZoneUtil


class PartyHood(Hood.Hood):
    notify = DirectNotifyGlobal.directNotify.newCategory('PartyHood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        Hood.Hood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.fsm = ClassicFSM.ClassicFSM('Hood', [
            State.State('start', self.enterStart, self.exitStart,
                        ['safeZoneLoader']),
            State.State('safeZoneLoader', self.enterSafeZoneLoader,
                        self.exitSafeZoneLoader, ['quietZone']),
            State.State('quietZone', self.enterQuietZone, self.exitQuietZone,
                        ['safeZoneLoader']),
            State.State('final', self.enterFinal, self.exitFinal, [])
        ], 'start', 'final')
        self.fsm.enterInitialState()
        self.id = PartyHood
        self.safeZoneLoaderClass = PartyLoader.PartyLoader
        self.partyActivityDoneEvent = 'partyActivityDone'
        self.storageDNAFile = 'phase_13/dna/storage_party_sz.dna'
        self.holidayStorageDNADict = {
            WINTER_DECORATIONS: ['phase_5.5/dna/winter_storage_estate.dna'],
            WACKY_WINTER_DECORATIONS:
            ['phase_5.5/dna/winter_storage_estate.dna']
        }
        self.skyFile = 'phase_3.5/models/props/TT_sky'
        self.popupInfo = None

    def load(self):
        Hood.Hood.load(self)

    def unload(self):
        del self.safeZoneLoaderClass
        if self.popupInfo:
            self.popupInfo.destroy()
            self.popupInfo = None

        Hood.Hood.unload(self)

    def enter(self, requestStatus):
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        self.accept(PartyGlobals.KICK_TO_PLAYGROUND_EVENT,
                    self.kickToPlayground)
        self.fsm.request(requestStatus['loader'], [requestStatus])

    def exit(self):
        if self.loader:
            self.loader.exit()
            self.loader.unload()
            del self.loader

        Hood.Hood.exit(self)

    def kickToPlayground(self, retCode):
        if retCode == 0:
            msg = TTLocalizer.PartyOverWarningNoName
            if hasattr(base, 'distributedParty') and base.distributedParty:
                name = base.distributedParty.hostName
                msg = TTLocalizer.PartyOverWarningWithName % TTLocalizer.GetPossesive(
                    name)

            self._PartyHood__popupKickoutMessage(msg)
            base.localAvatar.setTeleportAvailable(0)

        if retCode == 1:
            zoneId = base.localAvatar.lastHood
            self.doneStatus = {
                'loader': ZoneUtil.getBranchLoaderName(zoneId),
                'where': ZoneUtil.getToonWhereName(zoneId),
                'how': 'teleportIn',
                'hoodId': zoneId,
                'zoneId': zoneId,
                'shardId': None,
                'avId': -1
            }
            messenger.send(self.doneEvent)

    def _PartyHood__popupKickoutMessage(self, msg):
        if self.popupInfo is not None:
            self.popupInfo.destroy()
            self.popupInfo = None

        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'),
                         buttons.find('**/ChtBx_OKBtn_DN'),
                         buttons.find('**/ChtBx_OKBtn_Rllvr'))
        self.popupInfo = DirectFrame(
            parent=hidden,
            relief=None,
            state='normal',
            text=msg,
            frameSize=(-1, 1, -1, 1),
            text_wordwrap=10,
            geom=DGG.getDefaultDialogGeom(),
            geom_color=GlobalDialogColor,
            geom_scale=(0.88, 1, 0.75),
            geom_pos=(0, 0, -0.080000000000000002),
            text_scale=0.080000000000000002,
            text_pos=(0, 0.10000000000000001))
        DirectButton(
            self.popupInfo,
            image=okButtonImage,
            relief=None,
            text=TTLocalizer.EstatePopupOK,
            text_scale=0.050000000000000003,
            text_pos=(0.0, -0.10000000000000001),
            textMayChange=0,
            pos=(0.0, 0.0, -0.29999999999999999),
            command=self._PartyHood__handleKickoutOk)
        buttons.removeNode()
        self.popupInfo.reparentTo(aspect2d)

    def _PartyHood__handleKickoutOk(self):
        self.popupInfo.reparentTo(hidden)

    def handlePartyActivityDone(self):
        pass

    def loadLoader(self, requestStatus):
        loaderName = requestStatus['loader']
        if loaderName == 'safeZoneLoader':
            self.loader = self.safeZoneLoaderClass(
                self, self.fsm.getStateNamed('safeZoneLoader'),
                self.loaderDoneEvent)
            self.loader.load()

    def spawnTitleText(self, zoneId):
        pass

    def hideTitleTextTask(self, task):
        pass

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def startSky(self):
        SkyUtil.startCloudSky(self)
        if base.cloudPlatformsEnabled:
            self.loader.startCloudPlatforms()

    def stopSky(self):
        Hood.Hood.stopSky(self)
        self.loader.stopCloudPlatforms()
