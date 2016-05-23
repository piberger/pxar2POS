from CalibrationDataProvider import AbstractCalibrationDataProvider
import glob
import os

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataPath = "", nROCs = 16):
        self.dataPath = dataPath
        self.nROCs = nROCs

    def getRocDacs(self, ModuleID, options = {}):
        dacs = []

        pathParts = self.dataPath.split('/')
        pathParts.append("%s_FullQualification_*"%ModuleID)
        pathParts.append("*_%s"%(options['Test'] if 'Test' in options else 'm20'))

        if pathParts[0][-1] == ":":
            pathParts[0] = pathParts[0] + '/'
        globPath = os.path.join(*pathParts)
        folders = glob.glob(globPath)
        folders.sort()
        if len(folders) > 1:
            print "more than one folder found, using first one:"
            print " ->", folders[0]


        dacTable = {
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

        for iROC in range(self.nROCs):
            dacFileName = os.path.join(folders[0], "dacParameters%s_C%d.dat"%(options['DacSuffix'] if 'DacSuffix' in options else '', iROC))
            rocDACs = []
            if os.path.isfile(dacFileName):
                with open(dacFileName, 'r') as dacFile:
                    for line in dacFile:
                        dacLine = [x.lower() for x in line.strip().split(' ') if len(x) > 0]
                        if dacLine[1] in dacTable:
                            rocDACs.append({'Name': dacTable[dacLine[1]], 'Value': dacLine[2]})

            dacs.append({'ROC': iROC, 'DACs': rocDACs})
        return dacs


    def getTrimBits(self, ModuleID, iROC, options = {}):
        raise NotImplementedError('getTrimBits() not implemented!')

    def getTbmParameters(self, ModuleID, iROC, options={}):
        raise NotImplementedError('getTbmParameters() not implemented!')