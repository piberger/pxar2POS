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

        print "read data for module {moduleID}...".format(moduleID=moduleID)

        # read DAC parameters
        rocDACs = self.dataSource.getRocDacs(ModuleID=moduleID, options=testOptions)

        # read trimbits
        rocTrimbits = self.dataSource.getTrimBits(ModuleID=moduleID, options=testOptions)

        # read TBM parameters
        tbmParameters = self.dataSource.getTbmParameters(ModuleID=moduleID, options=testOptions)


        print "write data for module {moduleID}...".format(moduleID=moduleID)

        # write to pixel online format
        self.posWriter.writeDACs(moduleID, modulePosition, rocDACs)
        self.posWriter.writeTrim(moduleID, modulePosition, rocTrimbits)
        self.posWriter.writeTBM(moduleID, modulePosition, tbmParameters)
