from CalibrationDataProvider import CalibrationDataProviderFactory
from ModulePositionProvider.LocalData import ModulePositionProvider
from POSWriter.POSWriter import POSWriter
import traceback

class pxar2POSConverter(object):

    def __init__(self, options = {}):
        self.verbose = False

        # load module position table
        self.modulePositionTable = ModulePositionProvider(dataPath=options['ModulePositionTable'])

        # initialize data source
        dataSource = options['DataSource']
        cdpf = CalibrationDataProviderFactory.CalibrationDataProviderFactory()
        self.dataSource = cdpf.init(dataSource)

        # initialize pixel online format writer
        self.posWriter = POSWriter(outputPath=options['OutputPath'])


    def printError(self, errorMessage, tracebackMsg = None):
        if tracebackMsg:
            print "\x1b[31mERROR: %s\n%s\x1b[0m"%(errorMessage.strip(), tracebackMsg.strip())
        else:
            print "\x1b[31mERROR: %s\x1b[0m"%errorMessage.strip()


    # simple linear DAC interpolation
    def interpolateLinear(self, dacValueLow, dacValueHigh, temperature, temperatureLow=-20, temperatureHigh=17):
        deltaY = dacValueHigh - dacValueLow
        deltaX = temperatureHigh - temperatureLow
        m = deltaY / deltaX
        interpolatedValue = m * (temperature - temperatureLow) + dacValueLow
        if self.verbose:
            print "  low:", dacValueLow, " high:", dacValueHigh, " -> ",interpolatedValue
        return interpolatedValue


    def interpolateDAC(self, dacName, dacValueLow, dacValueHigh, temperature, temperatureLow=-20, temperatureHigh=17):
        if self.verbose:
            print "interpolate DAC:", dacName
        return self.interpolateLinear(dacValueLow, dacValueHigh, temperature, temperatureLow, temperatureHigh)


    def verifyModuleID(self, moduleID):
        good = True
        if not moduleID.startswith('M'):
            print "\x1b[31m -> module ID does not start with an M\x1b[0m"
            good = False

        if len(moduleID) != 5:
            print "\x1b[31m -> module ID does not have the correct length\x1b[0m"
            good = False

        if good:
            print " -> module ID is valid"

        return good


    def convertModuleData(self, moduleID, testOptions):

        # verify if ID is correct
        self.verifyModuleID(moduleID)

        # get module position in detector
        #     B/F      O/I    sector  layer   ladder   pos(inner=MOD1, outer=MOD4)
        #  -> ['BPix', 'BmO', 'SEC1', 'LYR2', 'LDR1H', 'MOD4']
        modulePosition = self.modulePositionTable.getModulePosition(moduleID)

        print "read/write data for module {moduleID}...".format(moduleID=moduleID)
        errorsOccurred = 0

        # check for temperature interpolation
        temperatureInterpolation = False
        interpolationTemperatureLow = -20
        interpolationTemperatureHigh = 17
        if 'tempnominal' in testOptions and testOptions['tempnominal'][0:3] not in ['m20', 'p17']:
            interpolationTemperature = float(testOptions['tempnominal'].replace('m', '-').replace('p', ''))
            temperatureInterpolation = True

        # read DAC parameters
        try:
            if temperatureInterpolation:
                testOptions['tempnominal'] = 'p17_1'
                rocDACsHigh = self.dataSource.getRocDacs(ModuleID=moduleID, options=testOptions)
                testOptions['tempnominal'] = 'm20_1'
                rocDACsLow = self.dataSource.getRocDacs(ModuleID=moduleID, options=testOptions)
            else:
                rocDACs = self.dataSource.getRocDacs(ModuleID=moduleID, options=testOptions)
        except Exception as e:
            self.printError("could not read DAC parameters", traceback.format_exc())
            errorsOccurred += 1

        # do temperature interpolation
        nDacsInterpolated = 0
        try:
            if temperatureInterpolation:
                rocDACs = []

                for rocDACsRocLow in rocDACsLow:
                    rocDACsRoc = []
                    rocPos = rocDACsRocLow['ROC']
                    for dacTuple in rocDACsRocLow['DACs']:

                        # low T DAC value
                        dacName = dacTuple['Name']
                        dacValueLow = float(dacTuple['Value'].strip())

                        # find high T DAC value
                        rocDACsRocHigh = [x for x in rocDACsHigh if x['ROC'] == rocPos]
                        if len(rocDACsRocHigh) != 1:
                            raise Exception('ROC not found for high T: %r / %r'%(rocPos, dacName))
                        dacValueHighList = [x for x in rocDACsRocHigh[0]['DACs'] if x['Name'] == dacName]
                        if len(rocDACsRocHigh) != 1:
                            raise Exception('DAC not found for high T: %r' % dacName)
                        dacValueHigh = float(dacValueHighList[0]['Value'].strip())

                        # interpolation
                        interpolatedValue = '%d'%int(self.interpolateDAC(dacName=dacName, dacValueLow=dacValueLow,
                            dacValueHigh=dacValueHigh, temperature=interpolationTemperature,
                            temperatureLow=interpolationTemperatureLow, temperatureHigh=interpolationTemperatureHigh))
                        nDacsInterpolated += 1

                        rocDACsRoc.append({'Name': dacName, 'Value': interpolatedValue})

                    rocDACs.append({'ROC': rocPos, 'DACs': rocDACsRoc})
                print " -> interpolated %d DACs to %1.2f C"%(nDacsInterpolated, interpolationTemperature)
        except Exception as e:
            self.printError("could not interpolate DACs", traceback.format_exc())
            errorsOccurred += 1


        # write DAC parameters
        try:
            self.posWriter.writeDACs(moduleID, modulePosition, rocDACs)
        except Exception as e:
            self.printError("could not write DAC parameters", traceback.format_exc())
            errorsOccurred += 1

        # trimbits
        try:
            # read trimbits
            moduleTrimbits = self.dataSource.getTrimBits(ModuleID=moduleID, options=testOptions)

            # write trimbits
            self.posWriter.writeTrim(moduleID, modulePosition, moduleTrimbits)
        except Exception as e:
            self.printError("could not read/write trimbits", traceback.format_exc())
            errorsOccurred += 1

        # TBM parameters
        try:
            # read TBM parameters
            tbmParameters = self.dataSource.getTbmParameters(ModuleID=moduleID, options=testOptions)

            # write TBM parameters to pixel online format
            self.posWriter.writeTBM(moduleID, modulePosition, tbmParameters)
        except Exception as e:
            self.printError("could not read/write TBM parameters", traceback.format_exc())
            errorsOccurred += 1

        # mask bits
        try:
            # read maskbits
            moduleMaskbits = self.dataSource.getMaskBits(ModuleID=moduleID, options=testOptions)

            # write maskbits
            self.posWriter.writeMask(moduleID, modulePosition, moduleMaskbits)
        except Exception as e:
            self.printError("could not read/write maskbits", traceback.format_exc())
            errorsOccurred += 1

        # readback
        try:
            # read readback
            moduleReadback = self.dataSource.getReadbackCalibration(ModuleID=moduleID, options=testOptions)

            # write readback
            self.posWriter.writeReadback(moduleID, modulePosition, moduleReadback)
        except Exception as e:
            self.printError("could not read/write readback calibration constants", traceback.format_exc())
            errorsOccurred += 1

        if errorsOccurred < 1:
            print " --> done."
        else:
            print "\x1b[31m --> done, but some errors occurred!!!\x1b[0m"