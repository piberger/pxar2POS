import os

class POSWriter(object):

    def __init__(self, outputPath = ""):
        self.columnWidth = 15
        self.rocSuffix = '_ROC%d'
        pathParts = outputPath.replace('\\','/').split('/')
        self.outputPath = os.path.join(*pathParts) + '/'
        try:
            os.mkdir(self.outputPath)
        except:
            pass
        self.nRows = 80
        self.nCols = 52

    def writeDACs(self, ModuleID, ModulePosition, rocsData):

        outputFileName = self.outputPath + "ROC_DAC_module_" + "_".join(ModulePosition) + ".dat"

        with open(outputFileName, 'w') as outputFile:
            for rocData in rocsData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:'.ljust(self.columnWidth) + "_".join(ModulePosition) + self.rocSuffix%rocID + '\n'

                # write header
                outputFile.write(rocHeaderLine)

                # write DACs
                for rocDAC in rocData['DACs']:
                    dacLine = ("%s:"%rocDAC['Name']).ljust(self.columnWidth) + rocDAC['Value'] + '\n'
                    outputFile.write(dacLine)

    def writeTrim(self, ModuleID, ModulePosition, trimData):
        outputFileName = self.outputPath + "ROC_Trims_module_" + "_".join(ModulePosition) + ".dat"

        with open(outputFileName, 'w') as outputFile:
            for rocData in trimData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:\t ' + "_".join(ModulePosition) + self.rocSuffix % rocID + '\n'

                # write header
                outputFile.write(rocHeaderLine)

                # write trim bits
                for iCol in range(self.nCols):
                    colTrims = ''
                    for iRow in range(self.nRows):
                        iPix = iCol * self.nRows + iRow
                        colTrims += '%1x'%rocData['Trims'][iPix]
                    colLine = "col%02d:   %s\n"%(iCol, colTrims)
                    outputFile.write(colLine)

