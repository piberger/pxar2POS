from CalibrationDataProvider import AbstractCalibrationDataProvider

import MySQLdb
import getpass
import urllib
import os
import json
try:
    import ROOT
except:
    pass

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataSource = None):
        # module/chip properties
        self.nROCs = 16
        self.nRows = 80
        self.nCols = 52
        self.nPix = self.nRows * self.nCols

        # default trim bit value. 0=lowest threshold, 15=highest threshold
        self.defaultTrim = 15

        # database url
        self.dataPath = dataSource
        self.dbServer = dataSource
        self.dbUrl = 'http://' + self.dbServer

        self.queryString = '''
SELECT * FROM test_fullmodule
JOIN test_fullmoduleanalysis ON test_fullmoduleanalysis.TEST_ID = test_fullmodule.LASTANALYSIS_ID
JOIN test_dacparameters ON test_dacparameters.FULLMODULEANALYSISTEST_ID = test_fullmoduleanalysis.TEST_ID
WHERE test_fullmodule.FULLMODULE_ID = %s AND tempnominal = %s AND TRIM_VALUE = %s ORDER BY ROC_POS;
        '''

        self.queryStringFTResults = '''
        SELECT FULLMODULE_ID, STEP, DATA_ID FROM view10
        WHERE FULLMODULE_ID = %s AND STEP = %s;
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

        # remote paths to download files
        self.remotePathTrimBitMap = '/Chips/Chip{iRoc}/TrimBitMap/TrimBitMap.root'
        self.remotePathTBM = '/TBM/KeyValueDictPairs.json'

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

    def getRocDacs(self, ModuleID, options = {}):
        dacs = []

        cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'
        TrimValue = options['TrimValue'] if 'TrimValue' in options else ''
        cursor.execute(self.queryString, (ModuleID, tempnominal, TrimValue))
        self.db.commit()
        rows = cursor.fetchall()
        for row in rows:
            rocDACs = []
            for dbDACName, POSName in self.dacTable.items():
                if dbDACName in row:
                    rocDACs.append({'Name': POSName, 'Value': '%d'%row[dbDACName]})

            if len([x for x in rocDACs if x['Name'] == 'TempRange']) < 1:
                rocDACs.append({'Name': 'TempRange', 'Value': '0'})

            if len([x for x in rocDACs if x['Name'] == 'Readback']) < 1:
                rocDACs.append({'Name': 'Readback', 'Value': '1'})

            dacs.append({'ROC': row['ROC_POS'], 'DACs': rocDACs})

        print " -> DACs read for {ModuleID}".format(ModuleID=ModuleID)
        return dacs


    def getRemoteResultsPath(self, ModuleID, options={}):

        cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'
        cursor.execute(self.queryStringFTResults, (ModuleID, tempnominal))
        self.db.commit()
        rowsRemoteDataPath = cursor.fetchall()
        if len(rowsRemoteDataPath) == 1:
            remoteModuleDataPath = self.dbUrl + rowsRemoteDataPath[0]['DATA_ID'].replace('file:', '')
            return remoteModuleDataPath
        else:
            return None


    def getTrimBits(self, ModuleID, options={}):
        trims = []

        remoteModuleDataPath = self.getRemoteResultsPath(ModuleID=ModuleID, options=options)
        if remoteModuleDataPath:
            for iRoc in range(self.nROCs):
                remoteFileName = self.remotePathTrimBitMap.format(iRoc=iRoc)
                localFileName = 'temp/TrimBitMap%sROC%d.root'%(ModuleID, iRoc)
                urllib.urlretrieve(remoteModuleDataPath + remoteFileName, localFileName)
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
            print " -> trim parameters read for {ModuleID}".format(ModuleID=ModuleID)
        return trims


    def getTbmParameters(self, ModuleID, options={}):
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

        remoteModuleDataPath = self.getRemoteResultsPath(ModuleID=ModuleID, options=options)
        if remoteModuleDataPath:
            remoteFileName = self.remotePathTBM
            localFileName = 'temp/TBM_%s.root'%(ModuleID)
            urllib.urlretrieve(remoteModuleDataPath + remoteFileName, localFileName)

            with open(localFileName) as data_file:
                data = json.load(data_file)

            try:
                tbmParameters.append({'Name': 'TBMPLLDelay', 'Value': int(data['Core0a_basee']['Value'].replace('0x', ''), 16)})
                tbmParameters.append({'Name': 'TBMADelay', 'Value': int(data['Core0a_basea']['Value'].replace('0x', ''), 16)})
                tbmParameters.append({'Name': 'TBMBDelay', 'Value': int(data['Core0b_basea']['Value'].replace('0x', ''), 16)})
            except:
                raise NameError("TBM/KeyValueDictPairs.json: can't read TBM parameters from JSON file")

            print " -> TBM parameters read for {ModuleID}".format(ModuleID=ModuleID)
        return tbmParameters
