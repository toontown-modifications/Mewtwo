from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from game.otp.avatar import ShadowCaster
from game.toontown.racing.KartDNA import *
from game.toontown.toonbase import TTLocalizer


class Kart(NodePath, ShadowCaster.ShadowCaster):
    notify = DirectNotifyGlobal.directNotify.newCategory('Kart')
    index = 0
    baseScale = 2.0
    RFWHEEL = 0
    LFWHEEL = 1
    RRWHEEL = 2
    LRWHEEL = 3
    wheelData = [{
        'node': 'wheel*Node2'
    }, {
        'node': 'wheel*Node1'
    }, {
        'node': 'wheel*Node3'
    }, {
        'node': 'wheel*Node4'
    }]
    ShadowScale = 2.5
    SFX_BaseDir = 'phase_6/audio/sfx/'
    SFX_KartStart = SFX_BaseDir + 'KART_Engine_start_%d.mp3'
    SFX_KartLoop = SFX_BaseDir + 'KART_Engine_loop_%d.wav'

    def __init__(self):
        NodePath.__init__(self)
        an = ActorNode('vehicle-test')
        anp = NodePath(an)
        NodePath.assign(self, anp)
        self.actorNode = an
        ShadowCaster.ShadowCaster.__init__(self, False)
        Kart.index += 1
        self.updateFields = []
        self.kartDNA = [-1] * getNumFields()
        self.kartAccessories = {
            KartDNA.ebType: None,
            KartDNA.spType: None,
            KartDNA.fwwType: (None, None),
            KartDNA.bwwType: (None, None)
        }
        self.texCount = 1

    def delete(self):
        self._Kart__stopWheelSpin()
        del self.kartDNA
        del self.updateFields
        self.kartLoopSfx.stop()
        NodePath.removeNode(self)
        ShadowCaster.ShadowCaster.delete(self)

    def getKartBounds(self):
        return self.geom[0].getTightBounds()

    def generateKart(self, forGui=0):
        self.LODnode = FadeLODNode('lodNode')
        self.LODpath = self.attachNewNode(self.LODnode)
        self.LODnode.setFadeTime(0.14999999999999999)
        self.geom = {}
        self.pitchNode = {}
        self.toonNode = {}
        self.rotateNode = self.attachNewNode('rotate')
        levelIn = [
            base.config.GetInt('lod1-in', 30),
            base.config.GetInt('lod2-in', 80),
            base.config.GetInt('lod2-in', 200)
        ]
        levelOut = [
            base.config.GetInt('lod1-out', 0),
            base.config.GetInt('lod2-out', 30),
            base.config.GetInt('lod2-out', 80)
        ]
        lodRequired = 3
        if forGui:
            lodRequired = 1
            levelIn[0] = base.config.GetInt('lod1-in', 2500)
            levelIn[1] = base.config.GetInt('lod1-out', 0)

        self.toonSeat = NodePath('toonSeat')
        for level in range(lodRequired):
            self._Kart__createLODKart(level)
            self.LODnode.addSwitch(levelIn[level], levelOut[level])

        self.setScale(self.baseScale)
        self.flattenMedium()
        for level in range(lodRequired):
            self.toonSeat = self.toonSeat.instanceTo(self.toonNode[level])

        self.LODpath.reparentTo(self.rotateNode)
        tempNode = NodePath('tempNode')
        self.accGeomScale = tempNode.getScale(
            self.pitchNode[0]) * self.baseScale
        tempNode.removeNode()
        self._Kart__applyBodyColor()
        self._Kart__applyEngineBlock()
        self._Kart__applySpoiler()
        self._Kart__applyFrontWheelWells()
        self._Kart__applyBackWheelWells()
        self._Kart__applyRims()
        self._Kart__applyDecals()
        self._Kart__applyAccessoryColor()
        self.wheelCenters = []
        self.wheelBases = []
        for wheel in self.wheelData:
            center = self.geom[0].find('**/' + wheel['node'])
            self.wheelCenters.append(center)
            wheelBase = center.getParent().attachNewNode('wheelBase')
            wheelBase.setPos(center.getPos())
            wheelBase.setZ(0)
            self.wheelBases.append(wheelBase)

        self.wheelBaseH = self.wheelCenters[0].getH()
        self._Kart__startWheelSpin()
        self.setWheelSpinSpeed(0)
        if not forGui:
            self.shadowJoint = self.geom[0]
            self.initializeDropShadow()
            self.setActiveShadow()
            self.dropShadow.setScale(self.ShadowScale)
        else:
            self.shadowJoint = self.LODpath
            self.initializeDropShadow()
            self.setActiveShadow()
            self.dropShadow.setScale(1.3, 3, 1)
        kartType = self.kartDNA[KartDNA.bodyType]
        self.kartStartSfx = base.loadSfx(self.SFX_KartStart % kartType)
        self.kartLoopSfx = base.loadSfx(self.SFX_KartLoop % kartType)
        self.kartLoopSfx.setLoop()

    def _Kart__createLODKart(self, level):
        kartBodyPath = getKartModelPath(self.kartDNA[KartDNA.bodyType], level)
        self.geom[level] = loader.loadModel(kartBodyPath)
        self.geom[level].reparentTo(self.LODpath)
        self.geom[level].setH(180)
        self.geom[level].setPos(0.0, 0, 0.025000000000000001)
        self.pitchNode[level] = self.geom[level].find('**/suspensionNode')
        self.toonNode[level] = self.geom[level].find('**/toonNode')
        scale = 1.0 / self.pitchNode[level].getScale()[0]
        scale /= self.baseScale
        self.toonNode[level].setScale(scale)
        h = (180 + self.pitchNode[level].getH()) % 360
        self.toonNode[level].setH(h)
        pos = Point3(0, -1.3, -7)
        self.toonNode[level].setPos(pos)

    def resetGeomPos(self):
        for level in self.geom.keys():
            self.geom[level].setPos(0, 0, 0.025000000000000001)

    def _Kart__update(self):
        for field in self.updateFields:
            if field == KartDNA.bodyType:
                if hasattr(self, 'geom'):
                    for kart in self.geom:
                        self.geom[kart].removeNode()
                        self._Kart__createLODKart(kart)
                        self.geom[kart].reparentTo(self.rotateNode)

                    self._Kart__applyBodyColor()
                    self._Kart__applyEngineBlock()
                    self._Kart__applySpoiler()
                    self._Kart__applyFrontWheelWells()
                    self._Kart__applyRims()
                    self._Kart__applyDecals()
                    self._Kart__applyAccessoryColor()
                else:
                    raise Exception(
                        'Kart::__update - Has this method been called before generateKart?'
                    )
            hasattr(self, 'geom')
            if field == KartDNA.bodyColor:
                self._Kart__applyBodyColor()
                continue
            if field == KartDNA.accColor:
                self._Kart__applyAccessoryColor()
                continue
            if field == KartDNA.ebType:
                if self.kartAccessories[KartDNA.ebType] is not None:
                    name = self.kartAccessories[KartDNA.ebType].getName()
                    for key in self.geom.keys():
                        self.geom[key].find('**/%s' % name).removeNode()

                    self.kartAccessories[KartDNA.ebType].removeNode()
                    self.kartAccessories[KartDNA.ebType] = None

                self._Kart__applyEngineBlock()
                continue
            if field == KartDNA.spType:
                if self.kartAccessories[KartDNA.spType] is not None:
                    name = self.kartAccessories[KartDNA.spType].getName()
                    for key in self.geom.keys():
                        self.geom[key].find('**/%s' % name).removeNode()

                    self.kartAccessories[KartDNA.spType].removeNode()
                    self.kartAccessories[KartDNA.spType] = None

                self._Kart__applySpoiler()
                continue
            if field == KartDNA.fwwType:
                if self.kartAccessories[KartDNA.fwwType] != (None, None):
                    (left, right) = self.kartAccessories[KartDNA.fwwType]
                    for key in self.geom.keys():
                        self.geom[key].find(
                            '**/%s' % left.getName()).removeNode()
                        self.geom[key].find(
                            '**/%s' % right.getName()).removeNode()

                    left.removeNode()
                    right.removeNode()
                    self.kartAccessories[KartDNA.fwwType] = (None, None)

                self._Kart__applyFrontWheelWells()
                continue
            if field == KartDNA.bwwType:
                if self.kartAccessories[KartDNA.bwwType] != (None, None):
                    (left, right) = self.kartAccessories[KartDNA.bwwType]
                    for key in self.geom.keys():
                        self.geom[key].find(
                            '**/%s' % left.getName()).removeNode()
                        self.geom[key].find(
                            '**/%s' % right.getName()).removeNode()

                    left.removeNode()
                    right.removeNode()
                    self.kartAccessories[KartDNA.bwwType] = (None, None)

                self._Kart__applyBackWheelWells()
                continue
            if field == KartDNA.rimsType:
                self._Kart__applyRims()
            elif field == KartDNA.decalType:
                self._Kart__applyDecals()

            self._Kart__applyAccessoryColor()

        self.updateFields = []

    def updateDNAField(self, field, fieldValue):
        if field == KartDNA.bodyType:
            self.setBodyType(fieldValue)
        elif field == KartDNA.bodyColor:
            self.setBodyColor(fieldValue)
        elif field == KartDNA.accColor:
            self.setAccessoryColor(fieldValue)
        elif field == KartDNA.ebType:
            self.setEngineBlockType(fieldValue)
        elif field == KartDNA.spType:
            self.setSpoilerType(fieldValue)
        elif field == KartDNA.fwwType:
            self.setFrontWheelWellType(fieldValue)
        elif field == KartDNA.bwwType:
            self.setBackWheelWellType(fieldValue)
        elif field == KartDNA.rimsType:
            self.setRimType(fieldValue)
        elif field == KartDNA.decalType:
            self.setDecalType(fieldValue)

        self.updateFields.append(field)
        self._Kart__update()

    def _Kart__applyBodyColor(self):
        if self.kartDNA[KartDNA.bodyColor] == InvalidEntry:
            bodyColor = getDefaultColor()
        else:
            bodyColor = getAccessory(self.kartDNA[KartDNA.bodyColor])
        for kart in self.geom:
            kartBody = self.geom[kart].find('**/chasse')
            kartBody.setColorScale(bodyColor)

    def _Kart__applyAccessoryColor(self):
        if self.kartDNA[KartDNA.accColor] == InvalidEntry:
            accColor = getDefaultColor()
        else:
            accColor = getAccessory(self.kartDNA[KartDNA.accColor])
        for kart in self.geom:
            hoodDecal = self.geom[kart].find('**/hoodDecal')
            rightSideDecal = self.geom[kart].find('**/rightSideDecal')
            leftSideDecal = self.geom[kart].find('**/leftSideDecal')
            hoodDecal.setColorScale(accColor)
            rightSideDecal.setColorScale(accColor)
            leftSideDecal.setColorScale(accColor)

        for type in [KartDNA.ebType, KartDNA.spType]:
            model = self.kartAccessories.get(type, None)
            if model is not None and not model.find('**/vertex').isEmpty():
                if self.kartDNA[KartDNA.accColor] == InvalidEntry:
                    accColor = getDefaultColor()
                else:
                    accColor = getAccessory(self.kartDNA[KartDNA.accColor])
                model.find('**/vertex').setColorScale(accColor)
                continue

        for type in [KartDNA.fwwType, KartDNA.bwwType]:
            (lModel, rModel) = self.kartAccessories.get(type, (None, None))
            if lModel is not None and not lModel.find('**/vertex').isEmpty():
                if self.kartDNA[KartDNA.accColor] == InvalidEntry:
                    accColor = getDefaultColor()
                else:
                    accColor = getAccessory(self.kartDNA[KartDNA.accColor])
                lModel.find('**/vertex').setColorScale(accColor)
                rModel.find('**/vertex').setColorScale(accColor)
                continue

    def _Kart__applyEngineBlock(self):
        ebType = self.kartDNA[KartDNA.ebType]
        if ebType == InvalidEntry:
            return None

        ebPath = getAccessory(ebType)
        attachNode = getAccessoryAttachNode(ebType)
        model = loader.loadModel(ebPath)
        self.kartAccessories[KartDNA.ebType] = model
        model.setScale(self.accGeomScale)
        if not model.find('**/vertex').isEmpty():
            if self.kartDNA[KartDNA.accColor] == InvalidEntry:
                accColor = getDefaultColor()
            else:
                accColor = getAccessory(self.kartDNA[KartDNA.accColor])
            model.find('**/vertex').setColorScale(accColor)

        for kart in self.geom:
            engineBlockNode = self.geom[kart].find('**/%s' % attachNode)
            model.setPos(engineBlockNode.getPos(self.pitchNode[kart]))
            model.setHpr(engineBlockNode.getHpr(self.pitchNode[kart]))
            model.instanceTo(self.pitchNode[kart])

    def _Kart__applySpoiler(self):
        spType = self.kartDNA[KartDNA.spType]
        if spType == InvalidEntry:
            return None

        spPath = getAccessory(spType)
        attachNode = getAccessoryAttachNode(spType)
        model = loader.loadModel(spPath)
        self.kartAccessories[KartDNA.spType] = model
        model.setScale(self.accGeomScale)
        for kart in self.geom:
            spoilerNode = self.geom[kart].find('**/%s' % attachNode)
            model.setPos(spoilerNode.getPos(self.pitchNode[kart]))
            model.setHpr(spoilerNode.getHpr(self.pitchNode[kart]))
            model.instanceTo(self.pitchNode[kart])

    def _Kart__applyRims(self):
        if self.kartDNA[KartDNA.rimsType] == InvalidEntry:
            rimTexPath = getAccessory(getDefaultRim())
        else:
            rimTexPath = getAccessory(self.kartDNA[KartDNA.rimsType])
        rimTex = loader.loadTexture('%s.jpg' % rimTexPath,
                                    '%s_a.rgb' % rimTexPath)
        for kart in self.geom:
            leftFrontWheelRim = self.geom[kart].find('**/leftFrontWheelRim')
            rightFrontWheelRim = self.geom[kart].find('**/rightFrontWheelRim')
            leftRearWheelRim = self.geom[kart].find('**/leftRearWheelRim')
            rightRearWheelRim = self.geom[kart].find('**/rightRearWheelRim')
            rimTex.setMinfilter(Texture.FTLinearMipmapLinear)
            leftFrontWheelRim.setTexture(rimTex, self.texCount)
            rightFrontWheelRim.setTexture(rimTex, self.texCount)
            leftRearWheelRim.setTexture(rimTex, self.texCount)
            rightRearWheelRim.setTexture(rimTex, self.texCount)

        self.texCount += 1

    def _Kart__applyFrontWheelWells(self):
        fwwType = self.kartDNA[KartDNA.fwwType]
        if fwwType == InvalidEntry:
            return None

        fwwPath = getAccessory(fwwType)
        attachNode = getAccessoryAttachNode(fwwType)
        leftAttachNode = attachNode % 'left'
        rightAttachNode = attachNode % 'right'
        leftModel = loader.loadModel(fwwPath)
        rightModel = loader.loadModel(fwwPath)
        self.kartAccessories[KartDNA.fwwType] = (leftModel, rightModel)
        if not leftModel.find('**/vertex').isEmpty():
            if self.kartDNA[KartDNA.accColor] == InvalidEntry:
                accColor = getDefaultColor()
            else:
                accColor = getAccessory(self.kartDNA[KartDNA.accColor])
            leftModel.find('**/vertex').setColorScale(accColor)
            rightModel.find('**/vertex').setColorScale(accColor)

        for kart in self.geom:
            leftNode = self.geom[kart].find('**/%s' % leftAttachNode)
            rightNode = self.geom[kart].find('**/%s' % rightAttachNode)
            leftNodePath = leftModel.instanceTo(self.pitchNode[kart])
            leftNodePath.setPos(rightNode.getPos(self.pitchNode[kart]))
            leftNodePath.setHpr(rightNode.getHpr(self.pitchNode[kart]))
            leftNodePath.setScale(self.accGeomScale)
            leftNodePath.setSx(-1.0 * leftNodePath.getSx())
            leftNodePath.setTwoSided(True)
            rightNodePath = rightModel.instanceTo(self.pitchNode[kart])
            rightNodePath.setPos(leftNode.getPos(self.pitchNode[kart]))
            rightNodePath.setHpr(leftNode.getHpr(self.pitchNode[kart]))
            rightNodePath.setScale(self.accGeomScale)

    def _Kart__applyBackWheelWells(self):
        bwwType = self.kartDNA[KartDNA.bwwType]
        if bwwType == InvalidEntry:
            return None

        bwwPath = getAccessory(bwwType)
        attachNode = getAccessoryAttachNode(bwwType)
        leftAttachNode = attachNode % 'left'
        rightAttachNode = attachNode % 'right'
        leftModel = loader.loadModel(bwwPath)
        rightModel = loader.loadModel(bwwPath)
        self.kartAccessories[KartDNA.bwwType] = (leftModel, rightModel)
        if not leftModel.find('**/vertex').isEmpty():
            if self.kartDNA[KartDNA.accColor] == InvalidEntry:
                accColor = getDefaultColor()
            else:
                accColor = getAccessory(self.kartDNA[KartDNA.accColor])
            leftModel.find('**/vertex').setColorScale(accColor)
            rightModel.find('**/vertex').setColorScale(accColor)

        for kart in self.geom:
            leftNode = self.geom[kart].find('**/%s' % leftAttachNode)
            rightNode = self.geom[kart].find('**/%s' % rightAttachNode)
            leftNodePath = leftModel.instanceTo(self.pitchNode[kart])
            leftNodePath.setPos(rightNode.getPos(self.pitchNode[kart]))
            leftNodePath.setHpr(rightNode.getHpr(self.pitchNode[kart]))
            leftNodePath.setScale(self.accGeomScale)
            leftNodePath.setSx(-1.0 * leftNodePath.getSx())
            leftNodePath.setTwoSided(True)
            rightNodePath = rightModel.instanceTo(self.pitchNode[kart])
            rightNodePath.setPos(leftNode.getPos(self.pitchNode[kart]))
            rightNodePath.setHpr(leftNode.getHpr(self.pitchNode[kart]))
            rightNodePath.setScale(self.accGeomScale)

    def _Kart__applyDecals(self):
        if self.kartDNA[KartDNA.decalType] != InvalidEntry:
            decalId = getAccessory(self.kartDNA[KartDNA.decalType])
            kartDecal = getDecalId(self.kartDNA[KartDNA.bodyType])
            hoodDecalTex = loader.loadTexture(
                'phase_6/maps/%s_HoodDecal_%s.jpg' % (kartDecal, decalId),
                'phase_6/maps/%s_HoodDecal_%s_a.rgb' % (kartDecal, decalId))
            sideDecalTex = loader.loadTexture(
                'phase_6/maps/%s_SideDecal_%s.jpg' % (kartDecal, decalId),
                'phase_6/maps/%s_SideDecal_%s_a.rgb' % (kartDecal, decalId))
            hoodDecalTex.setMinfilter(Texture.FTLinearMipmapLinear)
            sideDecalTex.setMinfilter(Texture.FTLinearMipmapLinear)
            for kart in self.geom:
                hoodDecal = self.geom[kart].find('**/hoodDecal')
                rightSideDecal = self.geom[kart].find('**/rightSideDecal')
                leftSideDecal = self.geom[kart].find('**/leftSideDecal')
                hoodDecal.setTexture(hoodDecalTex, self.texCount)
                rightSideDecal.setTexture(sideDecalTex, self.texCount)
                leftSideDecal.setTexture(sideDecalTex, self.texCount)
                hoodDecal.show()
                rightSideDecal.show()
                leftSideDecal.show()

        else:
            for kart in self.geom:
                hoodDecal = self.geom[kart].find('**/hoodDecal')
                rightSideDecal = self.geom[kart].find('**/rightSideDecal')
                leftSideDecal = self.geom[kart].find('**/leftSideDecal')
                hoodDecal.hide()
                rightSideDecal.hide()
                leftSideDecal.hide()

        self.texCount += 1

    def rollSuspension(self, roll):
        for kart in self.pitchNode:
            self.pitchNode[kart].setR(roll)

    def pitchSuspension(self, pitch):
        for kart in self.pitchNode:
            self.pitchNode[kart].setP(pitch)

    def getDNA(self):
        return self.kartDNA

    def setDNA(self, dna):
        if self.kartDNA != [-1] * getNumFields():
            for field in xrange(len(self.kartDNA)):
                if dna[field] != self.kartDNA[field]:
                    self.updateDNAField(field, dna[field])
                    continue

            return None

        self.kartDNA = dna

    def setBodyType(self, bodyType):
        self.kartDNA[KartDNA.bodyType] = bodyType

    def getBodyType(self):
        return self.kartDNA[KartDNA.bodyType]

    def setBodyColor(self, bodyColor):
        self.kartDNA[KartDNA.bodyColor] = bodyColor

    def getBodyColor(self):
        return self.kartDNA[KartDNA.bodyColor]

    def setAccessoryColor(self, accColor):
        self.kartDNA[KartDNA.accColor] = accColor

    def getAccessoryColor(self):
        return self.kartDNA[KartDNA.accColor]

    def setEngineBlockType(self, ebType):
        self.kartDNA[KartDNA.ebType] = ebType

    def getEngineBlockType(self):
        return self.kartDNA[KartDNA.ebType]

    def setSpoilerType(self, spType):
        self.kartDNA[KartDNA.spType] = spType

    def getSpoilerType(self):
        return self.kartDNA[KartDNA.spType]

    def setFrontWheelWellType(self, fwwType):
        self.kartDNA[KartDNA.fwwType] = fwwType

    def getFrontWheelWellType(self):
        return self.kartDNA[KartDNA.fwwType]

    def setBackWheelWellType(self, bwwType):
        self.kartDNA[KartDNA.bwwType] = bwwType

    def getBackWheelWellType(self):
        return self.kartDNA[KartDNA.bwwType]

    def setRimType(self, rimsType):
        self.kartDNA[KartDNA.rimsType] = rimsType

    def getRimType(self):
        return self.kartDNA[KartDNA.rimsType]

    def setDecalType(self, decalType):
        self.kartDNA[KartDNA.decalType] = decalType

    def getDecalType(self):
        return self.kartDNA[KartDNA.decalType]

    def getGeomNode(self):
        return self.geom[0]

    def spinWheels(self, amount):
        newSpin = (self.oldSpinAmount + amount) % 360
        for wheelNode in self.wheelCenters:
            wheelNode.setP(newSpin)

        self.oldSpinAmount = newSpin

    def setWheelSpinSpeed(self, speed):
        pass

    def _Kart__startWheelSpin(self):
        self.oldSpinAmount = 0

    def _Kart__stopWheelSpin(self):
        pass

    def turnWheels(self, amount):
        amount += self.wheelBaseH
        node = self.wheelCenters[self.RFWHEEL]
        node.setH(amount)
        node = self.wheelCenters[self.LFWHEEL]
        node.setH(amount)

    def generateEngineStartTrack(self):
        length = self.kartStartSfx.length()

        def printVol():
            print self.kartLoopSfx.getVolume()

        track = Parallel(
            SoundInterval(self.kartStartSfx), Func(self.kartLoopSfx.play),
            LerpFunctionInterval(
                self.kartLoopSfx.setVolume,
                fromData=0,
                toData=0.40000000000000002,
                duration=length))
        return Sequence(track, Func(printVol))

    def generateEngineStopTrack(self, duration=0):
        track = Parallel(
            LerpFunctionInterval(
                self.kartLoopSfx.setVolume,
                fromData=0.40000000000000002,
                toData=0,
                duration=duration))
        return track
