from CalibrationDataProvider import AbstractCalibrationDataProvider
from PisaDB import CalibrationDataProvider as PisaDB

try:
    import MySQLdb
except:
    print "\x1b[31mcould not load module: MySQLdb\x1b[0m"
    print "run: 'pip install MySQL-python'"
    exit(0)

try:
    import ROOT
except:
    pass

class CalibrationDataProvider(PisaDB, AbstractCalibrationDataProvider):

    def __init__(self, dataSource=None, verbose=False):
        PisaDB.__init__(self, dataSource=dataSource, verbose=verbose)

        self.sqlBBvthrcomp = '''
SELECT inventory_fullmodule.FULLMODULE_ID, tempnominal, ROC_POS, BumpBonding_threshold
    FROM inventory_fullmodule
    INNER JOIN test_fullmodule ON inventory_fullmodule.LASTTEST_FULLMODULE=test_fullmodule.SUMMARY_ID
    INNER JOIN test_fullmoduleanalysis ON test_fullmodule.LASTANALYSIS_ID=test_fullmoduleanalysis.TEST_ID
    INNER JOIN test_performanceparameters ON test_performanceparameters.FULLMODULEANALYSISTEST_ID=test_fullmoduleanalysis.TEST_ID
    WHERE inventory_fullmodule.FULLMODULE_ID = '{ModuleID}' AND tempnominal LIKE '{tempnominal}%' AND TYPE='FullQualification'
    ORDER BY tempnominal, ROC_POS;
'''

        self.thresholdMargin = 5  # lower threshold a bit to go from 50% efficiency point to ~100% efficiency
        self.thresholdMax = 125  # don't go lower (=higher value) with the threshold to avoid noise

    def getBBvthrcomp(self, ModuleID, options):

        # read BB Vthrcomp value from DB
        tempnominal = options['tempnominal'] if 'tempnominal' in options else 'm20_1'
        sql = self.sqlBBvthrcomp.format(ModuleID=ModuleID, tempnominal=tempnominal)
        cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute(sql)
        self.db.commit()
        rows = cursor.fetchall()

        # take the first Vthrcomp DAC found for this temperature
        rocDacs = {}
        for row in rows:
            if row['ROC_POS'] not in rocDacs:
                rocDacs[row['ROC_POS']] = row['BumpBonding_threshold']
        return rocDacs

    def getRocDacs(self, ModuleID, options={}):

        # read the standard DAC settings from DB. This is important, to have to right Vana DAC matching the Vthrcomp found later
        moduleDACs = super(CalibrationDataProvider, self).getRocDacs(ModuleID, options)

        # read Vthrcomps for BB test
        bbVthcompValues = self.getBBvthrcomp(ModuleID, options)
        print bbVthcompValues

        # replace Vthrcomp DAC
        for rocDACs in moduleDACs:
            if rocDACs['ROC'] in bbVthcompValues:
                for dac in rocDACs['DACs']:
                    if dac['Name'] == 'VcThr':
                        newValueInt = int(bbVthcompValues[rocDACs['ROC']])+self.thresholdMargin
                        if newValueInt > self.thresholdMax:
                            newValueInt = self.thresholdMax
                        newDacValue = "%d"%(newValueInt)
                        print "VcThr:", dac['Value'], " -> ", newDacValue
                        dac['Value'] = newDacValue

        return moduleDACs


    def getTrimBits(self, ModuleID, options={}):
        return super(CalibrationDataProvider, self).getTrimBits(ModuleID, options)


    def getTbmParameters(self, ModuleID, options={}):
        return super(CalibrationDataProvider, self).getTbmParameters(ModuleID, options)


    def getMaskBits(self, ModuleID, options={}):
        return super(CalibrationDataProvider, self).getMaskBits(ModuleID, options)


    def getReadbackCalibration(self, ModuleID, options={}):
        return super(CalibrationDataProvider, self).getReadbackCalibration(ModuleID, options)