from CalibrationDataProvider.PisaDB import CalibrationDataProvider
from CalibrationDataProvider.LocalData import CalibrationDataProvider as LocalCalibrationDataProvider

from ModulePositionProvider.LocalData import ModulePositionProvider
from POSWriter.POSWriter import POSWriter

class pxar2POSConverter(object):

    def __init__(self, options = {}):

        # load module position table
        self.modulePositionTable = ModulePositionProvider(dataPath=options['ModulePositionTable'])

        # module data source
        dataSource = options['DataSource']
        if 'http://' in dataSource:
            dataSource = dataSource.split('http://')[1]

            # connect to Pisa DB
            self.dataSource = CalibrationDataProvider(dataSource=dataSource)
        else:
            # or fetch data locally
            self.dataSource = LocalCalibrationDataProvider(dataSource=dataSource)

        # initialize pixel online format writer
        self.posWriter = POSWriter(outputPath=options['OutputPath'])


    def convertModuleData(self, moduleID, testOptions):

        # get module position in detector
        #     B/F      O/I    sector  layer   ladder   pos
        #  -> ['BPix', 'BmO', 'SEC1', 'LYR2', 'LDR1H', 'MOD4']
        modulePosition = self.modulePositionTable.getModulePosition(moduleID)

        print "read/write data for module {moduleID}...".format(moduleID=moduleID)
        errorsOccurred = 0

        try:
            # read DAC parameters
            rocDACs = self.dataSource.getRocDacs(ModuleID=moduleID, options=testOptions)

            # write DAC parameters
            self.posWriter.writeDACs(moduleID, modulePosition, rocDACs)
        except Exception as e:
            print e
            print "ERROR: could not read/write DAC parameters"
            errorsOccurred += 1

        try:
            # read trimbits
            rocTrimbits = self.dataSource.getTrimBits(ModuleID=moduleID, options=testOptions)

            # write trimbits
            self.posWriter.writeTrim(moduleID, modulePosition, rocTrimbits)
        except Exception as e:
            print e
            print "ERROR: could not read/write trimbits"
            errorsOccurred += 1

        try:
            # read TBM parameters
            tbmParameters = self.dataSource.getTbmParameters(ModuleID=moduleID, options=testOptions)

            # write TBM parameters to pixel online format
            self.posWriter.writeTBM(moduleID, modulePosition, tbmParameters)
        except Exception as e:
            print e
            print "ERROR: could not read/write TBM parameters"
            errorsOccurred += 1


        if errorsOccurred < 1:
            print " --> done."
        else:
            print " --> done, but some errors occurred!!!"