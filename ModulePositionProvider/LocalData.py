from ModulePositionProvider import AbstractModulePositionProvider
import os

class ModulePositionProvider(AbstractModulePositionProvider):

    # modules.txt format (ID BPix/FPix BmO/BpO/BmI/BpI sector layer ladder pos) separated by space:
    # e.g. M2222 BPix BmO SEC1 LYR2 LDR1H MOD4

    def __init__(self, dataPath = ""):
        self.dataPath = dataPath

    def getModulePosition(self, ModuleID):
        pathParts = self.dataPath.split('/')

        if pathParts[0][-1] == ":":
            pathParts[0] = pathParts[0] + '/'
        modulesListFileName = os.path.join(*pathParts)

        modulePosition = []
        moduleFound = False
        if os.path.isfile(modulesListFileName):
            with open(modulesListFileName, 'r') as modulesListFile:
                for line in modulesListFile:
                    lineSplitted = [x for x in line.replace('\t', ' ').split(' ') if len(x) > 0]
                    if lineSplitted[0] == ModuleID:
                        modulePosition = lineSplitted[1:]
                        moduleFound = True

        modulePosition = [x.strip() for x in modulePosition if len(x.strip()) > 0]
        if moduleFound:
            print " -> module found:", ModuleID
            print " -> position: ", '/'.join(modulePosition)
        else:
            print " -> module not found:", ModuleID

        return modulePosition