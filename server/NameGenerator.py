from panda3d.core import *
from direct.directnotify.DirectNotifyGlobal import directNotify
import os

class NameGenerator:
    notify = directNotify.newCategory('NameGenerator')

    def __init__(self):
        self.nameDictionary = {}

        searchPath = DSearchPath()
        searchPath.appendDirectory(Filename('etc'))
        searchPath.appendDirectory(Filename('../new-otp/etc'))
        filename = Filename('NameMasterEnglish.txt')
        if vfs:
            found = vfs.resolveFilename(filename, searchPath)
        else:
            found = filename.resolveFilename(searchPath)
        if not found:
            self.notify.error('NameGenerator: Error opening name list text file.')
        if vfs:
            input = StreamReader(vfs.openReadFile(filename, 1), 1)
        else:
            input = open(filename.toOsSpecific(), 'r')
        currentLine = input.readline()
        while currentLine:
            if currentLine.lstrip()[0:1] != '#':
                a1 = currentLine.find('*')
                a2 = currentLine.find('*', a1 + 1)
                self.nameDictionary[int(currentLine[0:a1])] = (int(currentLine[a1 + 1:a2]), currentLine[a2 + 1:len(currentLine) - 1])
            currentLine = input.readline()

    def makeName(self, pattern):
        parts = []
        for p, f in pattern:
            part = self.nameDictionary.get(p, ('', ''))[1]
            if f:
                part = part[:1].upper() + part[1:]
            else:
                part = part.lower()

            parts.append(part)

        parts[2] += parts.pop(3)
        while '' in parts:
            parts.remove('')

        return ' '.join(parts)