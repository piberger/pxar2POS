from CalibrationDataProvider import AbstractCalibrationDataProvider
import glob
import os
import json

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataSource="", verbose=False):
        super(CalibrationDataProvider, self).__init__()
        self.verbose = verbose
        self.dataPath = dataSource
        self.dacTable = {
            'vdig': 'Vdd',
            'vana': 'Vana',
            'vsh': 'Vsh',
            'vcomp': 'Vcomp',
            'vwllpr': 'VwllPr',
            'vwllsh': 'VwllSh',
            'vhlddel': 'VHldDel',
            'vtrim': 'Vtrim',
            'vthrcomp': 'VcThr',
            'vibias_bus': 'VIbias_bus',
            'phoffset': 'PHOffset',
            'vcomp_adc': 'Vcomp_ADC',
            'phscale': 'PHScale',
            'vicolor': 'VIColOr',
            'vcal': 'Vcal',
            'caldel': 'CalDel',
            'ctrlreg': 'ChipContReg',
            'wbc': 'WBC',
            'readback': 'Readback',
        }
        self.defaultMask = 0

    def getLocalModuleDataPath(self, ModuleID, options = {}):

        pathParts = self.dataPath.split('/')
        pathParts.append("%s_FullQualification_*"%ModuleID)
        pathParts.append("*_%s"%(options['Test'] if 'Test' in options else 'm20'))

        if len(pathParts[0]) == 0 or pathParts[0][-1] == ":":
            pathParts[0] = pathParts[0] + '/'

        folders = []

        # then in the fulltest subfolders
        globPath = os.path.join(*pathParts)
        folders += glob.glob(globPath)
        folders.sort()

        # add Xray qualifications
        pathParts = self.dataPath.split('/')
        pathParts.append("%s_Xray*_*"%ModuleID)
        pathParts.append("*_%s"%options['tempnominal'])
        if len(pathParts[0]) == 0 or pathParts[0][-1] == ":":
            pathParts[0] = pathParts[0] + '/'
        globPath = os.path.join(*pathParts)
        foldersXray = glob.glob(globPath)
        if len(foldersXray) > 0:
            foldersXray.sort()
            folders += foldersXray

        # if not found, look in the given path itself
        # this can be used to give a parameter folder directly, but one should only select 1 module then!
        folders.append(self.dataPath)

        return folders


    def getRocDacs(self, ModuleID, options = {}):
        dacs = []

        localModuleDataPaths = self.getLocalModuleDataPath(ModuleID=ModuleID, options=options)

        dacsFound = False
        for localModuleDataPath in localModuleDataPaths:
            for iROC in range(self.nROCs):
                dacFileName = os.path.join(localModuleDataPath, "dacParameters%s_C%d.dat"%(options['TrimValue'] if 'TrimValue' in options else '', iROC))
                rocDACs = []
                if os.path.isfile(dacFileName):
                    with open(dacFileName, 'r') as dacFile:
                        for line in dacFile:
                            dacLine = [x.lower() for x in line.strip().split(' ') if len(x) > 0]
                            if dacLine[1] in self.dacTable:
                                rocDACs.append({'Name': self.dacTable[dacLine[1]], 'Value': dacLine[2]})
                    dacsFound = True
                    dacs.append({'ROC': iROC, 'DACs': rocDACs})
            if dacsFound:
                if len(localModuleDataPaths) > 1:
                    print "more than one folder found, using this one:"
                    print "  ->", localModuleDataPath
                break


        return dacs

    # ------------------------------------------------------------------------------------------------------------------
    # returns list: [{'ROC': 0, 'Masks': rocMasks}, ...]
    #               rocMasks = [0, 0, 0, ... ] list of mask-bits for 4160 pixels. 0=unmasked, 1=masked
    # ------------------------------------------------------------------------------------------------------------------
    def getMaskBits(self, ModuleID, options={}):
        masks = []
        print "  -> reading mask bits from database: Xray test"

        # get DACs
        localModuleDataPaths = self.getLocalModuleDataPath(ModuleID=ModuleID, options=options)

        for localModuleDataPath in localModuleDataPaths:
            maskFileName = localModuleDataPath + '/defaultMaskFile.dat'
            if os.path.isfile(maskFileName):
                # initialize with default
                rocMasks = []
                for iRoc in range(self.nROCs):
                    rocMask = []
                    for col in range(52):
                        rocMask.append([self.defaultMask]*80)
                    rocMasks.append(rocMask)

                with open(maskFileName, 'r') as maskFile:
                    maskLines = [x.strip() for x in maskFile.readlines() if not x.strip().startswith('#')]
                print "mask lines:", maskLines

                # how to Mask
                # pix 0 42 51
                # col 0 21
                # row 0 4
                # roc 0

                for maskLine in maskLines:
                    maskLineParts = [x for x in maskLine.split(' ') if len(x.strip())>0]
                    if maskLineParts[0] == 'pix':
                        rocMasks[int(maskLineParts[1])][int(maskLineParts[2])][int(maskLineParts[3])] = 1
                    elif maskLineParts[0] == 'col':
                        rocMasks[int(maskLineParts[1])][int(maskLineParts[2])] = [1]*80
                    elif maskLineParts[0] == 'row':
                        for col in range(52):
                            rocMasks[int(maskLineParts[1])][col][int(maskLineParts[2])] = 1
                    elif maskLineParts[0] == 'roc':
                        for col in range(52):
                            rocMasks[int(maskLineParts[1])][col] = [1]*80
                    else:
                        print "\x1b[31mERROR: illegal mask command:", maskLineParts[0], " -> ignored\x1b[0m"

                # flatten out mask bits
                for iRoc in range(self.nROCs):
                    rocMasksFlat = []
                    for col in range(52):
                        rocMasksFlat += rocMasks[iRoc][col]
                    masks.append({'ROC': iRoc, 'Masks': rocMasksFlat})
                break

        return masks


    def getTrimBits(self, ModuleID, options = {}):

        trims = []
        localModuleDataPaths = self.getLocalModuleDataPath(ModuleID=ModuleID, options=options)

        trimsFound = False
        for localModuleDataPath in localModuleDataPaths:
            for iROC in range(self.nROCs):
                trimFileName = os.path.join(localModuleDataPath, "trimParameters%s_C%d.dat" %(options['TrimValue'] if 'TrimValue' in options else '', iROC))
                rocTrims = [self.defaultTrim]*self.nPix
                if os.path.isfile(trimFileName):
                    trimsFound = True
                    with open(trimFileName, 'r') as trimFile:
                        for line in trimFile:
                            trimLine = [x.lower() for x in line.strip().split(' ') if len(x) > 0]
                            if trimLine[1].lower() == 'pix':
                                iPix = int(trimLine[2]) * self.nRows + int(trimLine[3])
                                rocTrims[iPix] = int(trimLine[0])
                            else:
                                raise NameError('invalid trim bits file format!')
                    trims.append({'ROC': iROC, 'Trims': rocTrims})
            if trimsFound:
                if len(localModuleDataPaths) > 1:
                    print "more than one folder found, using this one:"
                    print "  ->", localModuleDataPath
                break

        return trims

    # ------------------------------------------------------------------------------------------------------------------
    # read TBM register (hex) from JSON data and convert to decimal
    # ------------------------------------------------------------------------------------------------------------------
    def getFormattedTbmParameter(self, data, tbmId, tbmCore, tbmRegister):
        try:
            tbmParameterValue = int(data['Core{tbmId}{tbmCore}_{tbmRegister}'.format(tbmId=tbmId, tbmCore=tbmCore, tbmRegister=tbmRegister)]['Value'].replace('0x', ''), 16)

            if self.verbose:
                print '    -> TBM: Core{tbmId}{tbmCore}_{tbmRegister} = {value}'.format(tbmId=tbmId, tbmCore=tbmCore, tbmRegister=tbmRegister, value=tbmParameterValue)

            return tbmParameterValue
        except:
            raise NameError("TBM/KeyValueDictPairs.json: can't read TBM parameters from JSON file: Core{tbmId}{tbmCore}_{tbmRegister}".format(tbmId=tbmId, tbmCore=tbmCore, tbmRegister=tbmRegister))

    # ------------------------------------------------------------------------------------------------------------------
    # read all TBM registers for 1 TBM
    # ------------------------------------------------------------------------------------------------------------------
    def getSingleTbmParameters(self, ModuleID, options={}, tbmId = 0):
        tbmParameters = []

        tbmParameters.append({'Name': 'TBMABase0', 'Value': 0})
        tbmParameters.append({'Name': 'TBMBBase0', 'Value': 0})
        tbmParameters.append({'Name': 'TBMAAutoReset', 'Value': 0})
        tbmParameters.append({'Name': 'TBMBAutoReset', 'Value': 0})
        tbmParameters.append({'Name': 'TBMANoTokenPass', 'Value': 0})
        tbmParameters.append({'Name': 'TBMBNoTokenPass', 'Value': 0})
        tbmParameters.append({'Name': 'TBMADisablePKAMCounter', 'Value': 1})
        tbmParameters.append({'Name': 'TBMBDisablePKAMCounter', 'Value': 1})
        tbmParameters.append({'Name': 'TBMAPKAMCount', 'Value': 5})
        tbmParameters.append({'Name': 'TBMBPKAMCount', 'Value': 5})


        localModuleDataPaths = self.getLocalModuleDataPath(ModuleID=ModuleID, options=options)
        existingFiles = [x+'/TMB.json' for x in localModuleDataPaths if os.path.isfile(x+'/TMB.json')]

        # first try to look for JSON files
        if len(existingFiles) > 0:

            with open(existingFiles[0]) as data_file:
                data = json.load(data_file)

            try:
                tbmParameters.append(
                    {'Name': 'TBMPLLDelay', 'Value': self.getFormattedTbmParameter(data, tbmId, 'a', 'basee')})
                tbmParameters.append(
                    {'Name': 'TBMADelay', 'Value': self.getFormattedTbmParameter(data, tbmId, 'a', 'basea')})
                tbmParameters.append(
                    {'Name': 'TBMBDelay', 'Value': self.getFormattedTbmParameter(data, tbmId, 'b', 'basea')})
            except:
                raise NameError("TBM/KeyValueDictPairs.json: can't read TBM parameters from JSON file")

            print "  -> TBM parameters read for {ModuleID}".format(ModuleID=ModuleID)
        else:
            # if no JSON is found, use .dat file
            existingFilesDat = [x + '/tbmParameters_C%da.dat'%tbmId for x in localModuleDataPaths if os.path.isfile(x + '/tbmParameters_C%da.dat'%tbmId)]

            # pXar default values
            TBMPLLDelay = 52
            TBMADelay = 100
            TBMBDelay = 100

            if len(existingFilesDat) > 0:
                if len(existingFilesDat) > 1:
                    print "\x1b[31mWARNING: multiple input sources for TBM parameters found, using:\n",existingFilesDat[0],"\x1b[0m"
                valuesFound = []

                # core a
                with open(existingFilesDat[0], 'r') as datFile:
                    lines = datFile.readlines()
                for line in lines:
                    lineParts = [x for x in line.split(' ') if len(x.strip()) > 0]
                    if lineParts[1] == 'basee':
                        TBMPLLDelay = int(lineParts[2].split('0x')[1], 16)
                        valuesFound.append('basee')
                    elif lineParts[1] == 'basea':
                        TBMADelay = int(lineParts[2].split('0x')[1], 16)
                        valuesFound.append('basea_a')

                # core b
                coreBdatFile = existingFilesDat[0].replace('_C%da.dat'%tbmId, '_C%db.dat'%tbmId)
                with open(coreBdatFile, 'r') as datFile:
                    lines = datFile.readlines()
                for line in lines:
                    lineParts = [x for x in line.split(' ') if len(x.strip()) > 0]
                    if lineParts[1] == 'basea':
                        TBMBDelay = int(lineParts[2].split('0x')[1], 16)
                        valuesFound.append('basea_b')

                # check if all parameters have been found exactly once
                if 'basee' in valuesFound and 'basea_a' in valuesFound and 'basea_b' in valuesFound and len(valuesFound) == 3:
                    print "--> correctly read TBM parameters from .dat file"
                else:
                    print "\x1b[31mERROR: some TBM parameters were not found, using defaults for those\x1b[0m"

            else:
                print "WARNING: no TBM data found in database, using default 160/400 phases + channel delays"

            tbmParameters.append({'Name': 'TBMPLLDelay', 'Value': TBMPLLDelay})
            tbmParameters.append({'Name': 'TBMADelay', 'Value': TBMADelay})
            tbmParameters.append({'Name': 'TBMBDelay', 'Value': TBMBDelay})

        return tbmParameters

    # ------------------------------------------------------------------------------------------------------------------
    # read all TBM registers for all TBMs
    # ------------------------------------------------------------------------------------------------------------------
    def getTbmParameters(self, ModuleID, options={}):

        # for L1 modules: return parameters for both TBMs in a list
        if ModuleID.upper().startswith('M1'):
            return [self.getSingleTbmParameters(ModuleID, options, 0), self.getSingleTbmParameters(ModuleID, options, 1)]
        else:
            return self.getSingleTbmParameters(ModuleID, options, 0)


    # ------------------------------------------------------------------------------------------------------------------
    # returns list: [{'ROC': 0, 'ReadbackCalibration': readbackCalibrationRoc}, ...]
    #               readbackCalibrationRoc = [{'Name': readbackParameter, 'Value': parameterValue}, ...]
    # ------------------------------------------------------------------------------------------------------------------
    def getReadbackCalibration(self, ModuleID, options={}):
        readbackCalibration = []

        # get readback calibration from database fulltest results
        localModuleDataPaths = self.getLocalModuleDataPath(ModuleID=ModuleID, options=options)
        existingFiles = [x for x in localModuleDataPaths if os.path.isfile(x+'/Readback0.json')]

        if len(existingFiles) > 0:
            for iRoc in range(self.nROCs):
                localFileName = existingFiles[0] + '/Readback%d.json'%iRoc

                readbackCalibrationRoc = []

                if not os.path.isfile(localFileName):
                    print "\x1b[31mERROR: failed to download to JSON file %s\x1b[31m" % localFileName

                data = None
                try:
                    with open(localFileName) as data_file:
                        data = json.load(data_file)
                except:
                    print "\x1b[31mERROR: failed to load data from JSON file %s\x1b[31m" % localFileName

                if data:
                    for readbackParameter in self.readbackParameters:
                        try:
                            parameterValue = float(data[readbackParameter]['Value'])
                        except:
                            print "\x1b[31mERROR: failed to extract parameter '%s' for ROC%d from JSON file %s -> setting it to 0!\x1b[31m" % (
                            readbackParameter, iRoc, localFileName)
                            parameterValue = 0
                        readbackCalibrationRoc.append({'Name': readbackParameter, 'Value': parameterValue})

                readbackCalibration.append({'ROC': iRoc, 'ReadbackCalibration': readbackCalibrationRoc})
        return readbackCalibration