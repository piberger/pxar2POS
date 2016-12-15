import os

class POSWriter(object):

    def __init__(self, outputPath = "", configurationID = -1):

        try:
            self.configurationID = int(configurationID)
        except:
            self.configurationID = -1

        self.columnWidth = 15
        self.rocSuffix = '_ROC%d'
        pathParts = outputPath.replace('\\','/').split('/')
        self.outputPath = os.path.join(*pathParts) + '/'
        self.nRows = 80
        self.nCols = 52

        # output file names
        if self.configurationID < 0:
            self.outputFileNameDAC = "ROC_DAC_module_{Position}.dat"
            self.outputFileNameTrims = "ROC_Trims_module_{Position}.dat"
            self.outputFileNameTBM = "TBM_module_{Position}.dat"
            self.outputFileNameMasks = "ROC_Masks_module_{Position}.dat"
            self.outputFileNameReadback = "ROC_Iana_{Position}.dat"
        else:

            # initialize output directory
            try:
                os.mkdir(self.outputPath)
            except:
                pass

            # create output subfolders if necessary
            for folderName in ['dac', 'tbm', 'iana', 'mask', 'trim']:
                try:
                    os.mkdir(self.outputPath + '/%s'%folderName)
                except:
                    pass
                try:
                    os.mkdir(self.outputPath + '/%s/%d'%(folderName, self.configurationID))
                except:
                    pass

            self.outputFileNameDAC = "dac/%d/ROC_DAC_module_{Position}.dat"%self.configurationID
            self.outputFileNameTrims = "trim/%d/ROC_Trims_module_{Position}.dat"%self.configurationID
            self.outputFileNameTBM = "tbm/%d/TBM_module_{Position}.dat"%self.configurationID
            self.outputFileNameMasks = "mask/%d/ROC_Masks_module_{Position}.dat"%self.configurationID
            self.outputFileNameReadback = "iana/%d/ROC_Iana_{Position}.dat"%self.configurationID

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

        # assignment of ROCs to TBMs in L1 modules
        self.PseudoHalfModuleROCs = [
            [0, 1, 2, 3, 12, 13, 14, 15],
            [4, 5, 6, 7, 8, 9, 10, 11],
        ]


    # ------------------------------------------------------------------------------------------------------------------
    # check if L1 or L2/3/4 module
    # ------------------------------------------------------------------------------------------------------------------
    def isL1Module(self, ModuleID):
        return ModuleID.upper().startswith('M1')

    # ------------------------------------------------------------------------------------------------------------------
    # write single DAC file
    # ------------------------------------------------------------------------------------------------------------------
    def writeSingleDACFiles(self, rocsData, modulePositionString):

        outputFileName = self.outputPath + self.outputFileNameDAC.format(Position=modulePositionString)

        if len(rocsData) < 1:
            raise Exception("no ROC DAC parameters found!")

        with open(outputFileName, 'w') as outputFile:
            nLines = 0
            for rocData in rocsData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:'.ljust(self.columnWidth) + modulePositionString + self.rocSuffix%rocID + '\n'

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
    # write DAC file(s)
    # ------------------------------------------------------------------------------------------------------------------
    def writeDACs(self, ModuleID, ModulePosition, rocsData):

        if self.isL1Module(ModuleID):
            # write separate files for pseudo half-modules
            for i in range(2):
                self.writeSingleDACFiles([x for x in rocsData if x['ROC'] in self.PseudoHalfModuleROCs[i]], self.getFormattedHalfModuleName(ModulePosition, i))
        else:
            self.writeSingleDACFiles(rocsData, self.getFormattedModuleName(ModulePosition))

    # ------------------------------------------------------------------------------------------------------------------
    # write single trim bit file
    # ------------------------------------------------------------------------------------------------------------------
    def writeSingleTrimFile(self, trimData, modulePositionString):
        outputFileName = self.outputPath + self.outputFileNameTrims.format(Position=modulePositionString)

        if len(trimData) < 1:
            raise Exception("no ROCs with trimbit parameters found!")

        with open(outputFileName, 'w') as outputFile:
            for rocData in trimData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:\t ' + modulePositionString + self.rocSuffix % rocID + '\n'

                # write header
                outputFile.write(rocHeaderLine)

                # write trim bits
                for iCol in range(self.nCols):
                    colTrims = ''
                    for iRow in range(self.nRows):
                        iPix = iCol * self.nRows + iRow
                        colTrims += '%1x' % rocData['Trims'][iPix]
                    colLine = "col%02d:   %s\n" % (iCol, colTrims)
                    outputFile.write(colLine)
        print "  -> trimbits for {nRocs} ROCS written to '\x1b[34m{outputFileName}\x1b[0m'".format(nRocs=len(trimData),
                                                                                                   outputFileName=outputFileName)

    # ------------------------------------------------------------------------------------------------------------------
    # write trim bit file(s)
    # ------------------------------------------------------------------------------------------------------------------
    def writeTrim(self, ModuleID, ModulePosition, trimData):

        if self.isL1Module(ModuleID):
            # write separate files for pseudo half-modules
            for i in range(2):
                self.writeSingleTrimFile([x for x in trimData if x['ROC'] in self.PseudoHalfModuleROCs[i]], self.getFormattedHalfModuleName(ModulePosition, i))
        else:
            self.writeSingleTrimFile(trimData, self.getFormattedModuleName(ModulePosition))

    # ------------------------------------------------------------------------------------------------------------------
    # write single mask bit file
    # ------------------------------------------------------------------------------------------------------------------
    def writeSingleMaskFile(self, maskData, modulePositionString):
        outputFileName = self.outputPath + self.outputFileNameMasks.format(Position=modulePositionString)

        if len(maskData) < 1:
            raise Exception("no ROCs with trimbit parameters found!")

        with open(outputFileName, 'w') as outputFile:
            for rocData in maskData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:\t ' + modulePositionString + self.rocSuffix % rocID + '\n'

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
    # write mask bit file(s)
    # ------------------------------------------------------------------------------------------------------------------
    def writeMask(self, ModuleID, ModulePosition, maskData):

        if self.isL1Module(ModuleID):
            # write separate files for pseudo half-modules
            for i in range(2):
                self.writeSingleMaskFile([x for x in maskData if x['ROC'] in self.PseudoHalfModuleROCs[i]], self.getFormattedHalfModuleName(ModulePosition, i))
        else:
            self.writeSingleMaskFile(maskData, self.getFormattedModuleName(ModulePosition))

    # ------------------------------------------------------------------------------------------------------------------
    # write single TBM configuration file
    # ------------------------------------------------------------------------------------------------------------------
    def writeSingleTBMFile(self, tbmData, modulePositionString):
        outputFileName = self.outputPath + self.outputFileNameTBM.format(Position=modulePositionString)
        with open(outputFileName, 'w') as outputFile:
            headerLine = modulePositionString + '_ROC0\n'  # for some reason there has to be a 'ROC0' even for TBM configuration

            # write header
            outputFile.write(headerLine)

            # write values
            for tbmParameter in tbmData:
                line = self.dacFormat.format(Name=tbmParameter['Name'], Value=tbmParameter['Value'])
                outputFile.write(line)
        print "  -> TBM parameters written to '\x1b[34m{outputFileName}\x1b[0m'".format(outputFileName=outputFileName)

    # ------------------------------------------------------------------------------------------------------------------
    # get filename for L1 TBM files
    # ------------------------------------------------------------------------------------------------------------------
    # abuse (F)ullmodule/(H)alfmodule terminology for the two TBMs of a L1 modules:
    #  TBM0 (ROCs 0-3, 12-15) --> LDR*F
    #  TBM1 (ROCs 4-11)       --> LDR*H
    # ------------------------------------------------------------------------------------------------------------------
    def getFormattedHalfModuleName(self, ModulePosition, tbmId = 0):
        halfModuleSuffix = 'H' if tbmId == 1 else 'F'
        return "_".join([(x.strip()[0:-1] + halfModuleSuffix) if x.upper().startswith('LDR') else x for x in ModulePosition])

    # ------------------------------------------------------------------------------------------------------------------
    # get filename for TBM files
    # ------------------------------------------------------------------------------------------------------------------
    def getFormattedModuleName(self, ModulePosition):
        return "_".join(ModulePosition)

    # ------------------------------------------------------------------------------------------------------------------
    # write TBM(s) configuration files
    # ------------------------------------------------------------------------------------------------------------------
    def writeTBM(self, ModuleID, ModulePosition, tbmData):


        if len(tbmData) < 1:
            raise Exception("no ROCs with TBM parameters found!")

        if type(tbmData) != list:
            raise Exception("malformatted TBM data found")

        if type(tbmData[0]) == list:
            if not self.isL1Module(ModuleID):
                raise Exception("L1 module dual TBM data found, but module is not a L1 module!")

            print "  -> L1 module dual TBM data found, writing 2 files"
            for tbmId in range(2):
                self.writeSingleTBMFile(tbmData[tbmId], self.getFormattedHalfModuleName(ModulePosition, tbmId))

        else:
            if self.isL1Module(ModuleID):
                raise Exception("L2/3/4 module single TBM data found, but module is a L1 module!")
            self.writeSingleTBMFile(tbmData, self.getFormattedModuleName(ModulePosition))

    # ------------------------------------------------------------------------------------------------------------------
    # write single Readback calibration file
    # ------------------------------------------------------------------------------------------------------------------
    def writeSingleReadbackFile(self, readbackData, modulePositionString):
        outputFileName = self.outputPath + self.outputFileNameReadback.format(Position=modulePositionString)

        if len(readbackData) < 1:
            raise Exception("no ROCs with calibrated readback found!")

        with open(outputFileName, 'w') as outputFile:
            nLines = 0
            for rocData in readbackData:
                rocID = rocData['ROC']
                rocHeaderLine = 'ROC:'.ljust(self.columnWidth) + modulePositionString + self.rocSuffix % rocID + '\n'

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

    # ------------------------------------------------------------------------------------------------------------------
    # write Readback calibration file(s)
    # ------------------------------------------------------------------------------------------------------------------
    def writeReadback(self, ModuleID, ModulePosition, readbackData):

        if self.isL1Module(ModuleID):
            # write separate files for pseudo half-modules
            for i in range(2):
                self.writeSingleReadbackFile([x for x in readbackData if x['ROC'] in self.PseudoHalfModuleROCs[i]],
                                         self.getFormattedHalfModuleName(ModulePosition, i))
        else:
            self.writeSingleReadbackFile(readbackData, self.getFormattedModuleName(ModulePosition))
