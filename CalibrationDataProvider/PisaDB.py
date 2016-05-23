from CalibrationDataProvider import AbstractCalibrationDataProvider

import MySQLdb
import getpass
import urllib
import os

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataPath = "", nROCs = 16):
        self.dataPath = dataPath
        self.nROCs = nROCs
        self.nRows = 80
        self.nCols = 52
        self.nPix = self.nRows * self.nCols
        self.defaultTrim = 15

        self.dbServer = 'cmspixelprod.pi.infn.it'
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
            'READBACK': 'Readback',
        }
        try:
            os.mkdir('temp')
        except:
            raise

        Password = getpass.getpass()
        self.db=MySQLdb.connect(host=self.dbServer, user="reader", passwd=Password, db="prod_pixel")


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
            dacs.append({'ROC': row['ROC_POS'], 'DACs': rocDACs})

        return dacs


    def getTrimBits(self, ModuleID, options={}):
        trims = []

        cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'
        cursor.execute(self.queryStringFTResults, (ModuleID, tempnominal))
        self.db.commit()
        rowsRemoteDataPath = cursor.fetchall()
        if len(rowsRemoteDataPath) == 1:
            remoteModuleDataPath = self.dbUrl + rowsRemoteDataPath[0]['DATA_ID'].replace('file:', '')
            for iRoc in range(self.nROCs):
                remoteFileName = '/Chips/Chip%d/TrimBitMap/TrimBitMap.root'%iRoc
                urllib.urlretrieve(remoteModuleDataPath + remoteFileName, "temp/TrimBitMap%sROC%d.root"%(ModuleID, iRoc))
                rocTrims = [self.defaultTrim] * self.nPix

                # read trim file

                # todo: read file with root

                trims.append({'ROC': iRoc, 'Trims': rocTrims})

        return trims
