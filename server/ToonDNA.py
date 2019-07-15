from panda3d.core import *

toonHeadTypes = ['dls', 'dss', 'dsl', 'dll', 'cls', 'css', 'csl', 'cll', 'hls', 'hss', 'hsl', 'hll', 'mls', 'mss', 'rls', 'rss', 'rsl', 'rll', 'fls', 'fss', 'fsl', 'fll']
toonTorsoTypes = ['ss', 'ms', 'ls', 'sd', 'md', 'ld', 's', 'm', 'l']
toonLegTypes = ['s', 'm', 'l']

NumToColor = ['White', 'Peach', 'Bright Red', 'Red', 'Maroon', 'Sienna', 'Brown', 'Tan', 'Coral', 'Orange', 'Yellow', 'Cream', 'Citrine', 'Lime', 'Sea Green', 'Green', 'Light Blue', 'Aqua', 'Blue', 'Periwinkle', 'Royal Blue', 'Slate Blue', 'Purple', 'Lavender', 'Pink']

class ToonDNA:

    def makeFromNetString(self, string):
        try:
            dg = Datagram(string)
            dgi = DatagramIterator(dg)
            self.type = dgi.getFixedString(1)
            if self.type == 't':
                headIndex = dgi.getUint8()
                torsoIndex = dgi.getUint8()
                legsIndex = dgi.getUint8()
                self.head = toonHeadTypes[headIndex]
                self.torso = toonTorsoTypes[torsoIndex]
                self.legs = toonLegTypes[legsIndex]
                gender = dgi.getUint8()
                if gender == 1:
                    self.gender = 'm'
                else:
                    self.gender = 'f'
                self.topTex = dgi.getUint8()
                self.topTexColor = dgi.getUint8()
                self.sleeveTex = dgi.getUint8()
                self.sleeveTexColor = dgi.getUint8()
                self.botTex = dgi.getUint8()
                self.botTexColor = dgi.getUint8()
                self.armColor = dgi.getUint8()
                self.gloveColor = dgi.getUint8()
                self.legColor = dgi.getUint8()
                self.headColor = dgi.getUint8()

                return True
        except:
            return False

    def getToonName(self):
        color = NumToColor[self.headColor]

        if self.head[0] == 'd':
            color += ' Dog'
        elif self.head[0] == 'c':
            color += ' Cat'
        elif self.head[0] == 'm':
            color += ' Mouse'
        elif self.head[0] == 'h':
            color += ' Horse'
        elif self.head[0] == 'r':
            color += ' Rabbit'
        elif self.head[0] == 'f':
            color += ' Fowl'

        return color