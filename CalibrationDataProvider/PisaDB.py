from CalibrationDataProvider import AbstractCalibrationDataProvider

import MySQLdb
import getpass

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataPath = "", nROCs = 16):
        self.dataPath = dataPath
        self.nROCs = nROCs
        self.nRows = 80
        self.nCols = 52
        self.nPix = self.nRows * self.nCols
        self.defaultTrim = 15

        self.queryString = '''
SELECT * FROM test_fullmodule
JOIN test_fullmoduleanalysis ON test_fullmoduleanalysis.TEST_ID = test_fullmodule.LASTANALYSIS_ID
JOIN test_dacparameters ON test_dacparameters.FULLMODULEANALYSISTEST_ID = test_fullmoduleanalysis.TEST_ID
WHERE test_fullmodule.FULLMODULE_ID = %s AND tempnominal = %s AND TRIM_VALUE = %s ORDER BY ROC_POS;
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
        Password = getpass.getpass()
        self.db=MySQLdb.connect(host="cmspixelprod.pi.infn.it", user="reader", passwd=Password, db="prod_pixel")


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
