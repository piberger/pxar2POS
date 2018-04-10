from CalibrationDataProvider import AbstractCalibrationDataProvider

try:
    import MySQLdb
except:
    print "\x1b[31mcould not load module: MySQLdb\x1b[0m"
    print "run: 'pip install MySQL-python'"
    print "\x1b[31mcontinuing, but some features will not work without this module!\x1b[0m"

import getpass
import urllib
import os
import json
try:
    import ROOT
except:
    pass

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataSource=None, verbose=False):
        super(CalibrationDataProvider, self).__init__()

        self.verbose = verbose

        # database url
        self.dataPath = dataSource
        self.dbServer = dataSource.replace('http://', '')
        self.dbUrl = dataSource

        # remote paths to download files
        self.remotePathTrimBitMap = '/Chips/Chip{iRoc}/TrimBitMap/TrimBitMap.root'
        self.remotePathTBM = '/TBM/KeyValueDictPairs.json'
        self.remotePathReadbackJson = '/Chips/Chip{iRoc}/ReadbackCal/KeyValueDictPairs.json'

        self.queryStringFulltests = '''
            SELECT * FROM inventory_fullmodule
              JOIN test_fullmodulesummary ON test_fullmodulesummary.TEST_ID = LASTTEST_FULLMODULE
              JOIN test_fullmodule ON test_fullmodule.SUMMARY_ID = LASTTEST_FULLMODULE
              JOIN test_fullmoduleanalysis ON test_fullmoduleanalysis.TEST_ID = test_fullmodule.LASTANALYSIS_ID
            WHERE inventory_fullmodule.FULLMODULE_ID = %s AND tempnominal LIKE %s
            LIMIT 10;
        '''

        self.queryStringFulltests2 = '''
            SELECT * FROM inventory_fullmodule
              JOIN test_fullmodule ON test_fullmodule.FULLMODULE_ID = inventory_fullmodule.FULLMODULE_ID
              JOIN test_fullmoduleanalysis ON test_fullmoduleanalysis.TEST_ID = test_fullmodule.LASTANALYSIS_ID
              WHERE inventory_fullmodule.FULLMODULE_ID = %s AND tempnominal LIKE %s
              ORDER BY tempnominal, TIMESTAMP DESC
              LIMIT 10;
        '''

        self.queryStringReceptions = '''
            SELECT * FROM inventory_fullmodule
              JOIN test_fullmodulesummary ON test_fullmodulesummary.TEST_ID = LASTTEST_RECEPTION
              JOIN test_fullmodule ON test_fullmodule.SUMMARY_ID = LASTTEST_RECEPTION
              JOIN test_fullmoduleanalysis ON test_fullmoduleanalysis.TEST_ID = test_fullmodule.LASTANALYSIS_ID
            WHERE inventory_fullmodule.FULLMODULE_ID = %s
            LIMIT 10;
                '''

        self.queryStringFulltestDacs = '''
            SELECT * FROM test_dacparameters WHERE FULLMODULEANALYSISTEST_ID = %s AND TRIM_VALUE = %s
            ORDER BY ROC_POS
            LIMIT 16;
        '''

        self.queryStringFulltestData = '''
            SELECT * FROM test_data WHERE DATA_ID = %s
            LIMIT 1;
        '''

        self.queryStringXrayMaskedPixels = '''
            SELECT inventory_fullmodule.FULLMODULE_ID, LASTTEST_XRAY_HR, ROC_POS, ADDR_PIXELS_HOT FROM inventory_fullmodule INNER JOIN Test_FullModule_XRay_HR_Summary ON inventory_fullmodule.LASTTEST_XRAY_HR = Test_FullModule_XRay_HR_Summary.TEST_ID
              INNER JOIN Test_FullModule_XRay_HR_Roc_Analysis_Summary ON Test_FullModule_XRay_HR_Roc_Analysis_Summary.TEST_XRAY_HR_SUMMARY_ID = Test_FullModule_XRay_HR_Summary.TEST_ID AND Test_FullModule_XRay_HR_Roc_Analysis_Summary.PROCESSING_ID = Test_FullModule_XRay_HR_Summary.LAST_PROCESSING_ID
            WHERE inventory_fullmodule.FULLMODULE_ID = %s
            ORDER BY ROC_POS
            LIMIT 20;
'''

        self.dacTable = {
            'VDIG': 'Vdd',
            'VANA': 'Vana',
            'VSH': 'Vsh',
            'VCOMP': 'Vcomp',
            'VWLLPR': 'VwllPr',
            'VWLLSH': 'VwllSh',
            'VHLDDEL': 'VHldDel',
            'VTRIM': 'Vtrim',
            'VTHRCOMP': 'VcThr',
            'VIBIAS_BUS': 'VIbias_bus',
            'PHOFFSET': 'PHOffset',
            'VCOMP_ADC': 'Vcomp_ADC',
            'PHSCALE': 'PHScale',
            'VICOLOR': 'VIColOr',
            'VCAL': 'Vcal',
            'CALDEL': 'CalDel',
            'CTRLREG': 'ChipContReg',
            'WBC': 'WBC',
            'READBACK': 'Readback', #this does not exist in DB!
            'TEMPRANGE': 'TempRange', #this does not exist in DB!
        }

        # connect to database
        self.dbUser = "reader"
        self.dbName = "prod_pixel"
        print "connect to {dbUser}@{dbServer} database: {dbName}".format(dbUser=self.dbUser, dbServer=self.dbServer, dbName=self.dbName)
        Password = self.getDbPassword(self.dbUser)
        self.db = MySQLdb.connect(host=self.dbServer, user=self.dbUser, passwd=Password, db=self.dbName)

        try:
            self.saveDbPassword(self.dbUser, Password)
        except:
            print "could not save DB password to local file 'db.auth'"

        # temp folder for downloads from database
        try:
            os.mkdir('temp')
        except:
            pass

    def getDbPassword(self, username):
        dbPassFileName = 'db.auth'
        password = ''
        passwordFound = False
        try:
            if os.path.isfile(dbPassFileName):
                with open(dbPassFileName, 'r') as dbPassFile:
                    for line in dbPassFile:
                        if line.split(':')[0].strip() == username:
                            password = line.split(':')[1].strip() if len(line.split(':')) > 1 else ''
                            passwordFound = True
                            break
        except:
            pass

        if not passwordFound:
            password = getpass.getpass()

        return password

    def saveDbPassword(self, username, password):
        dbPassFileName = 'db.auth'
        with open(dbPassFileName, 'w') as dbPassFile:
            line = username + ':' + password
            dbPassFile.write(line)

    def getFulltestRow(self, ModuleID, tempnominal):

        cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # get list of fulltests
        if self.verbose:
            print "\x1b[32mSQL:", self.queryStringFulltests%(ModuleID, tempnominal + '%'), "\x1b[0m"
        cursor.execute(self.queryStringFulltests, (ModuleID, tempnominal + '%'))
        self.db.commit()
        rows = cursor.fetchall()
        if len(rows) < 1:
            print "ERROR: no FullQualification found including tempnominal=", tempnominal," => search for single Fulltests "
            if self.verbose:
                print "\x1b[32mSQL:", self.queryStringFulltests2 % (ModuleID, tempnominal + '%'), "\x1b[0m"
            cursor.execute(self.queryStringFulltests2, (ModuleID, tempnominal + '%'))
            self.db.commit()
            rows = cursor.fetchall()
            if len(rows) < 1:
                print "\x1b[31mERROR: no Fulltests found for tempnominal=", tempnominal,"\x1b[0m"
                return None

        if len(rows) > 1:
            print "WARNING: multiple Fulltests found for tempnominal=", tempnominal, " using the first one"

        row = rows[0] # take first one
        return row


    def getReceptionRow(self, ModuleID, tempnominal):

        cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # get list of fulltests
        cursor.execute(self.queryStringReceptions, (ModuleID,))
        self.db.commit()
        rows = cursor.fetchall()
        if len(rows) < 1:
            print self.queryStringReceptions
            print "\x1b[31mERROR: no Rception tests found for tempnominal=", tempnominal,"\x1b[0m"
            return None

        if len(rows) > 1:
            print "WARNING: multiple Rception tests found for tempnominal=", tempnominal, " using the first one"

        row = rows[0] # take first one
        return row


    def getRocDacs(self, ModuleID, options = {}):

        # initialize
        dacs = []
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'
        TrimValue = options['TrimValue'] if 'TrimValue' in options else '-1'
        row = self.getFulltestRow(ModuleID, tempnominal)

        if row:
            fulltestAnalysisId = row['LASTANALYSIS_ID']
            try:
                print "  -> Fulltest analysis ID: ", fulltestAnalysisId
                print "  -> tempnominal: ", tempnominal, " -> ", row['tempnominal']
                print "  -> Temperature: ", row['TEMPVALUE']
                print "  -> Analysis MoReWeb version: ", row['MACRO_VERSION']
            except:
                pass

            # get DACs
            cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            cursor.execute(self.queryStringFulltestDacs, (fulltestAnalysisId, TrimValue))
            self.db.commit()
            rows = cursor.fetchall()
            nDACs = 0
            for row in rows:
                rocDACs = []
                for dbDACName, POSName in self.dacTable.items():
                    if dbDACName in row:
                        rocDACs.append({'Name': POSName, 'Value': '%d'%row[dbDACName]})
                        nDACs += 1

                if len([x for x in rocDACs if x['Name'] == 'TempRange']) < 1:
                    rocDACs.append({'Name': 'TempRange', 'Value': '0'})

                if len([x for x in rocDACs if x['Name'] == 'Readback']) < 1:
                    rocDACs.append({'Name': 'Readback', 'Value': '1'})

                dacs.append({'ROC': row['ROC_POS'], 'DACs': rocDACs})
                if self.verbose:
                    try:
                        print "    -> ROC", row['ROC_POS']
                        for i in rocDACs:
                            print "      -> DAC: {DAC: <13}{Value: <10}".format(DAC=i['Name'], Value=i['Value'])
                    except:
                        pass
            print "  -> {nDACs} DACs read for {ModuleID}".format(ModuleID=ModuleID, nDACs=nDACs)

        else:
            print "ERROR: Fulltest not found"

        return dacs

    # ------------------------------------------------------------------------------------------------------------------
    # get path of MoReWeb analysis results on DB server
    # ------------------------------------------------------------------------------------------------------------------
    def getRemoteResultsPath(self, ModuleID, options={}):

        # initialize
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'

        # get fulltest analysis ID and data ID
        row = self.getFulltestRow(ModuleID, tempnominal)

        if row:
            dataId = row['test_fullmoduleanalysis.DATA_ID']
            print "  -> Fulltest analysis ID: ", row['LASTANALYSIS_ID']
            print "  -> data ID: ", dataId

            # get remote data path for the data ID
            cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            cursor.execute(self.queryStringFulltestData, (dataId, ))
            self.db.commit()
            rows = cursor.fetchall()
            if len(rows) > 0:
                remoteModuleDataPath = self.dbUrl + rows[0]['PFNs'].replace('file:', '')
                print "  -> remote path: ", remoteModuleDataPath
                return remoteModuleDataPath
        else:
            return None

    # ------------------------------------------------------------------------------------------------------------------
    # get path of MoReWeb analysis results on DB server for Reception test
    # ------------------------------------------------------------------------------------------------------------------
    def getRemoteResultsPathReception(self, ModuleID, options={}):

        # initialize
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'

        # get fulltest analysis ID and data ID
        row = self.getReceptionRow(ModuleID, tempnominal)

        if row:
            dataId = row['test_fullmoduleanalysis.DATA_ID']
            print "  -> Reception analysis ID: ", row['LASTANALYSIS_ID']
            print "  -> data ID: ", dataId

            # get remote data path for the data ID
            cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            cursor.execute(self.queryStringFulltestData, (dataId, ))
            self.db.commit()
            rows = cursor.fetchall()
            if len(rows) > 0:
                remoteModuleDataPath = self.dbUrl + rows[0]['PFNs'].replace('file:', '')
                print "  -> reception remote path: ", remoteModuleDataPath
                return remoteModuleDataPath
        else:
            return None

    # ------------------------------------------------------------------------------------------------------------------
    # wrapper for urllib to download files from DB
    # ------------------------------------------------------------------------------------------------------------------
    def downloadFile(self, remoteUrl, localFileName):
        attempts = 5
        success = False
        while attempts > 0 and not success:
            try:
                urllib.urlretrieve(remoteUrl, localFileName)
                success = True
            except Exception as e:
                print "ERROR: ", e, "=> RETRY"
                attempts -= 1

        if not success:
            print "\x1b[31mERROR: could not download file:", remoteUrl, "\x1b[0m"

        return success


    # ------------------------------------------------------------------------------------------------------------------
    # returns list: [{'ROC': 0, 'Trims': rocTrims}, ...]
    #               rocTrims = [..] list of trim-bits for 4160 pixels
    # ------------------------------------------------------------------------------------------------------------------
    def getTrimBits(self, ModuleID, options={}):
        trims = []

        # if untrimmed configuration is requested, set all trimbits to default value
        if 'TrimValue' in options and int(options['TrimValue']) < 0:
            print "WARNING: TrimValue < 0, setting all trimbits to ", self.defaultTrim, " instead of obtaining them from database!"
            for iRoc in range(self.nROCs):
                rocTrims = [self.defaultTrim] * self.nPix
                trims.append({'ROC': iRoc, 'Trims': rocTrims})
            return trims

        # otherwise get trimbits from database fulltest results
        remoteModuleDataPath = self.getRemoteResultsPath(ModuleID=ModuleID, options=options)
        if remoteModuleDataPath:
            for iRoc in range(self.nROCs):
                remoteFileName = self.remotePathTrimBitMap.format(iRoc=iRoc)
                localFileName = 'temp/TrimBitMap%sROC%d.root'%(ModuleID, iRoc)

                if not self.downloadFile(remoteModuleDataPath + remoteFileName, localFileName):
                    print "\x1b[31m:ERROR: could not download file with trimbits\x1b[0m"
                    raise Exception("could not download trimbit file")

                rocTrims = [self.defaultTrim] * self.nPix

                # read trim file
                RootFile = ROOT.TFile.Open(localFileName)
                RootFileCanvas = RootFile.Get("c1")
                PrimitivesList = RootFileCanvas.GetListOfPrimitives()
                histName = 'TrimBitMap'
                ClonedROOTObject = None
                HistogramFound = False
                for i in range(0, PrimitivesList.GetSize()):
                    if PrimitivesList.At(i).GetName().find(histName) > -1:
                        ClonedROOTObject = PrimitivesList.At(i).Clone('TH2DTrimBitMap%sROC%d'%(ModuleID, iRoc))
                        try:
                            ClonedROOTObject.SetDirectory(0)
                        except:
                            pass
                        HistogramFound = True
                        RootFile.Close()
                        break
                if HistogramFound:
                    nBinsX = ClonedROOTObject.GetXaxis().GetNbins()
                    nBinsY = ClonedROOTObject.GetYaxis().GetNbins()
                    assert nBinsX == self.nCols and nBinsY == self.nRows

                    for col in range(self.nCols):
                        for row in range(self.nRows):
                            rocTrims[col * self.nRows + row] = ClonedROOTObject.GetBinContent(1 + col, 1 + row)

                trims.append({'ROC': iRoc, 'Trims': rocTrims})
            print "  -> trim parameters read for {ModuleID}".format(ModuleID=ModuleID)
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

        # this returns the path to a JSON file created by Moreweb on the DB side, containing TBM settings
        remoteModuleDataPath = self.getRemoteResultsPath(ModuleID=ModuleID, options=options)

        if remoteModuleDataPath:
            remoteFileName = self.remotePathTBM
            localFileName = 'temp/TBM_%s.json' % (ModuleID)
            if not self.downloadFile(remoteModuleDataPath + remoteFileName, localFileName):
                print "\x1b[31m:ERROR: could not download file with TBM parameters\x1b[0m"
                raise Exception("could not download TBM file")

            with open(localFileName) as data_file:
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
            print "WARNING: no TBM data found in database, using default 160/400 phases + channel delays"
            tbmParameters.append({'Name': 'TBMPLLDelay', 'Value': 52})
            tbmParameters.append({'Name': 'TBMADelay', 'Value': 100})
            tbmParameters.append({'Name': 'TBMBDelay', 'Value': 100})

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
    # returns list: [{'ROC': 0, 'Masks': rocMasks}, ...]
    #               rocMasks = [0, 0, 0, ... ] list of mask-bits for 4160 pixels. 0=unmasked, 1=masked
    # ------------------------------------------------------------------------------------------------------------------
    def getMaskBits(self, ModuleID, options={}):
        masks = []
        print "  -> reading mask bits from database: Xray test"

        # get DACs
        cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute(self.queryStringXrayMaskedPixels, (ModuleID, ))
        self.db.commit()
        rows = cursor.fetchall()

        if len(rows) < 1:
            print "WARNING: no X-ray test found for this module, using unmasked configuration!"

            for iRoc in range(self.nROCs):
                rocMasks = [self.defaultMask] * self.nPix
                masks.append({'ROC': iRoc, 'Masks': rocMasks})
        else:
            if len(rows) != self.nROCs:
                if self.verbose:
                    print '-'*80, '\n',rows,'\n'
                raise NameError("ERROR: DB returns data for less/more ROCs than exist on the module!")

            print "    -> XRAY HR test ID", rows[0]['LASTTEST_XRAY_HR']
            for row in rows:
                rocMasks = [self.defaultMask] * self.nPix
                maskedPixelsString = row['ADDR_PIXELS_HOT'].strip().strip('[').strip(']')
                if len(maskedPixelsString) > 0:
                    maskedPixels = [[int(y) for y in x.strip().strip('(').strip(')').split(',')] for x in maskedPixelsString.split('),')]
                else:
                    maskedPixels = []
                if self.verbose:
                    if len(maskedPixels) > 0:
                        print "%d pixels MASKED on ROC %d:"%(len(maskedPixels), int(row['ROC_POS'])), maskedPixels
                for maskedPixel in maskedPixels:
                    rocMasks[maskedPixel[1]*self.nRows + maskedPixel[2]] = 1

                masks.append({'ROC': int(row['ROC_POS']), 'Masks': rocMasks})

        return masks

    # ------------------------------------------------------------------------------------------------------------------
    # returns list: [{'ROC': 0, 'ReadbackCalibration': readbackCalibrationRoc}, ...]
    #               readbackCalibrationRoc = [{'Name': readbackParameter, 'Value': parameterValue}, ...]
    # ------------------------------------------------------------------------------------------------------------------
    def getReadbackCalibration(self, ModuleID, options = {}):
        readbackCalibration = []

        # get readback calibration from database fulltest results
        remoteModuleDataPath = self.getRemoteResultsPath(ModuleID=ModuleID, options=options)
        if remoteModuleDataPath:
            for iRoc in range(self.nROCs):
                remoteFileName = self.remotePathReadbackJson.format(iRoc=iRoc)
                localFileName = 'temp/%s_ReadbackCalibration_ROC%d.json'%(ModuleID, iRoc)
                self.downloadFile(remoteModuleDataPath + remoteFileName, localFileName)

                readbackCalibrationRoc = []

                if not os.path.isfile(localFileName):
                    print "\x1b[31mERROR: failed to download to JSON file %s\x1b[31m"%localFileName

                data = None
                try:
                    with open(localFileName) as data_file:
                        data = json.load(data_file)
                except:
                    print "\x1b[31mERROR: failed to load data from JSON file %s\x1b[31m"%localFileName

                # check if readback has been calibrated in FullQualification
                if True or (data and 'ReadbackCalibrated' in data and data['ReadbackCalibrated']['Value'].lower().strip() != 'true'):
                    print "INFO: readback not calibrated flag has been set for this module - reception test results will be used."

                    # try to obtain calibration constants from Reception test (always at +17)
                    remoteModuleDataPathReception = self.getRemoteResultsPathReception(ModuleID=ModuleID, options=options)

                    if remoteModuleDataPathReception:
                        if not self.downloadFile(remoteModuleDataPathReception + remoteFileName, localFileName):
                            print "\x1b[31m:ERROR: could not download file with readback calibration from reception test\x1b[0m"
                            raise Exception("could not download reception readback file")

                        try:
                            with open(localFileName) as data_file:
                                data = json.load(data_file)
                            print "INFO: Reception test found!"
                        except:
                            print "\x1b[31mERROR: failed to load data from JSON file %s (reception test)\x1b[31m" % localFileName
                    else:
                        print "\x1b[31mERROR: no Reception test found for this module!\x1b[0m"

                if data:
                    for readbackParameter in self.readbackParameters:
                        try:
                            parameterValue = float(data[readbackParameter]['Value'])
                        except:
                            print "\x1b[31mERROR: failed to extract parameter '%s' for ROC%d from JSON file %s -> setting it to 0!\x1b[31m" % (readbackParameter, iRoc, localFileName)
                            parameterValue = 0
                        readbackCalibrationRoc.append({'Name': readbackParameter, 'Value': parameterValue})

                readbackCalibration.append({'ROC': iRoc, 'ReadbackCalibration': readbackCalibrationRoc})
        return readbackCalibration