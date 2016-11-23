import os

class POSWriter(object):

    def __init__(self, outputPath = ""):
        self.columnWidth = 15
        self.rocSuffix = '_ROC%d'
        pathParts = outputPath.replace('\\','/').split('/')
        self.outputPath = os.path.join(*pathParts) + '/'
        self.nRows = 80
        self.nCols = 52

        # output file names
        self.outputFileNameDAC = "ROC_DAC_module_{Position}.dat"
        self.outputFileNameTrims = "ROC_Trims_module_{Position}.dat"
        self.outputFileNameTBM = "TBM_module_{Position}.dat"
        self.outputFileNameMasks = "ROC_Masks_module_{Position}.dat"
        self.outputFileNameReadback = "ROC_Iana_{Position}.dat"

        # output format
        self.dacFormat = '{Name}: {Value}\n'
        self.readbackFormat = '{Name}: {Value:.6f}\n'

        # define the order in which DAC parameters are written
        self.rocDACOrder = ['Vdd', 'Vana', 'Vsh', 'Vcomp', 'VwllPr', 'VwllSh', 'VHldDel', 'Vtrim', 'VcThr',
                       'VIbias_bus', 'PHOffset', 'Vcomp_ADC', 'PHScale', 'VIColOr', 'Vcal', 'CalDel',
                       'TempRange', 'WBC', 'ChipContReg', 'Readback']

        # define the order in which readback calibration constants are written
        self.readbackParametersOrder = ['par0vd', 'par1vd', 'par0va', 'par1va', 'par0rbia', 'par1rbia', 'par0tbia',
                                   'par1tbia', 'par2tbia', 'par0ia', 'par1ia', 'par2ia']

        # initialize output directory
        try:
            os.mkdir(self.outputPath)
        except:
            pass
    # ------------------------------------------------------------------------------------------------------------------
    # write DAC file
    # ------------------------------------------------------------------------------------------------------------------
    def writeDACs(self, ModuleID, ModulePosition, rocsData):

        outputFileName = self.outputPath + self.outputFileNameDAC.format(Position="_".join(ModulePosition))

        if len(rocsData) < 1:
            raise Exception("no ROC DAC parameters found!")

        with open(outputFileName, 'w') as outputFile:
            nLines = 0
            for rocData in rocsData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:'.ljust(self.columnWidth) + "_".join(ModulePosition) + self.rocSuffix%rocID + '\n'

                # write header
                outputFile.write(rocHeaderLine)

                # sort DACs
                rocDACs = rocData['DACs']

                rocDACs.sort(key=lambda dac: self.rocDACOrder.index(dac['Name']) if dac['Name'] in self.rocDACOrder else 999)

                # write DACs
                for rocDAC in rocData['DACs']:
                    dacLine = ("%s:"%rocDAC['Name']).ljust(self.columnWidth) + rocDAC['Value'] + '\n'
                    outputFile.write(dacLine)
                nLines = len(rocData['DACs'])
        print "  -> {nLines} parameters for {nRocs} ROCS written to '\x1b[34m{outputFileName}\x1b[0m'".format(nLines=nLines, nRocs=len(rocsData), outputFileName=outputFileName)
        if nLines < 1:
            raise Exception("no ROC DAC parameters written!")

    # ------------------------------------------------------------------------------------------------------------------
    # write trim bit file
    # ------------------------------------------------------------------------------------------------------------------
    def writeTrim(self, ModuleID, ModulePosition, trimData):
        outputFileName = self.outputPath + self.outputFileNameTrims.format(Position="_".join(ModulePosition))

        if len(trimData) < 1:
            raise Exception("no ROCs with trimbit parameters found!")

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
        print "  -> trimbits for {nRocs} ROCS written to '\x1b[34m{outputFileName}\x1b[0m'".format(nRocs=len(trimData), outputFileName=outputFileName)

    # ------------------------------------------------------------------------------------------------------------------
    # write mask bit file
    # ------------------------------------------------------------------------------------------------------------------
    def writeMask(self, ModuleID, ModulePosition, maskData):
        outputFileName = self.outputPath + self.outputFileNameMasks.format(Position="_".join(ModulePosition))

        if len(maskData) < 1:
            raise Exception("no ROCs with trimbit parameters found!")

        with open(outputFileName, 'w') as outputFile:
            for rocData in maskData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:\t ' + "_".join(ModulePosition) + self.rocSuffix % rocID + '\n'

                # write header
                outputFile.write(rocHeaderLine)

                # write trim bits
                for iCol in range(self.nCols):
                    colMasks = ''
                    for iRow in range(self.nRows):
                        iPix = iCol * self.nRows + iRow
                        colMasks += '%1x'%rocData['Masks'][iPix]
                    colLine = "col%02d:   %s\n"%(iCol, colMasks)
                    outputFile.write(colLine)
        print "  -> maskbits for {nRocs} ROCS written to '\x1b[34m{outputFileName}\x1b[0m'".format(nRocs=len(maskData), outputFileName=outputFileName)

    # ------------------------------------------------------------------------------------------------------------------
    # write TBM configuration files
    # ------------------------------------------------------------------------------------------------------------------
    def writeTBM(self, ModuleID, ModulePosition, tbmData):
        modulePositionString = "_".join(ModulePosition)
        outputFileName = self.outputPath + self.outputFileNameTBM.format(Position=modulePositionString)

        if len(tbmData) < 1:
            raise Exception("no ROCs with TBM parameters found!")

        with open(outputFileName, 'w') as outputFile:
            headerLine = modulePositionString + '_ROC0\n' # for some reason there has to be a 'ROC0' even for TBM configuration

            # write header
            outputFile.write(headerLine)

            for tbmParameter in tbmData:
                line = self.dacFormat.format(Name=tbmParameter['Name'], Value=tbmParameter['Value'])
                outputFile.write(line)
        print "  -> TBM parameters written to '\x1b[34m{outputFileName}\x1b[0m'".format(outputFileName=outputFileName)

    # ------------------------------------------------------------------------------------------------------------------
    # write Readback calibration files
    # ------------------------------------------------------------------------------------------------------------------
    def writeReadback(self, ModuleID, ModulePosition, readbackData):
        modulePositionString = "_".join(ModulePosition)
        outputFileName = self.outputPath + self.outputFileNameReadback.format(Position=modulePositionString)

        if len(readbackData) < 1:
            raise Exception("no ROCs with calibrated readback found!")

        with open(outputFileName, 'w') as outputFile:
            nLines = 0
            for rocData in readbackData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:'.ljust(self.columnWidth) + "_".join(ModulePosition) + self.rocSuffix % rocID + '\n'

                # write header
                outputFile.write(rocHeaderLine)

                # sort readback calibration constants
                readbackParameters = rocData['ReadbackCalibration']
                readbackParameters.sort(key=lambda par: self.readbackParametersOrder.index(par['Name']) if par['Name'] in self.readbackParametersOrder else 999)

                # write readback calibration constants
                for readbackParameter in readbackParameters:
                    parLine = self.readbackFormat.format(Name=readbackParameter['Name'], Value=readbackParameter['Value'])
                    outputFile.write(parLine)

                nLines = len(readbackParameters)
        message = "  -> {nLines} readback parameters for {nRocs} ROCS written to '\x1b[34m{outputFileName}\x1b[0m'"
        print message.format(nLines=nLines, nRocs=len(readbackData), outputFileName=outputFileName)

        if nLines < 1:
            raise Exception("no ROC readback parameters written!")