from CalibrationDataProvider import AbstractCalibrationDataProvider
import os

class CalibrationDataProvider(AbstractCalibrationDataProvider):

    def __init__(self, dataSource = None):
        super(CalibrationDataProvider, self).__init__()

    # initialize DACs with default value
    def getRocDacs(self, ModuleID, options = {}):
        dacs = []
        for roc in range(self.nROCs):
            rocDACs = [
                {'Name': 'Vdd', 'Value': '6'},
                {'Name': 'Vana', 'Value': '81'},
                {'Name': 'Vsh', 'Value': '30'},
                {'Name': 'Vcomp', 'Value': '12'},
                {'Name': 'VwllPr', 'Value': '150'},
                {'Name': 'VwllSh', 'Value': '150'},
                {'Name': 'VHldDel', 'Value': '250'},
                {'Name': 'Vtrim', 'Value': '0'},
                {'Name': 'VcThr', 'Value': '85'},
                {'Name': 'VIbias_bus', 'Value': '30'},
                {'Name': 'PHOffset', 'Value': '185'},
                {'Name': 'Vcomp_ADC', 'Value': '50'},
                {'Name': 'PHScale', 'Value': '65'},
                {'Name': 'VIColOr', 'Value': '100'},
                {'Name': 'Vcal', 'Value': '200'},
                {'Name': 'CalDel', 'Value': '133'},
                {'Name': 'TempRange', 'Value': '0'},
                {'Name': 'WBC', 'Value': '100'},
                {'Name': 'ChipContReg', 'Value': '0'},
                {'Name': 'Readback', 'Value': '0'},
            ]
            dacs.append({'ROC': roc, 'DACs': rocDACs})
        print "  -> created list of default DACs for %d ROCs"%self.nROCs
        return dacs

    # default trimbit configuration
    def getTrimBits(self, ModuleID, options={}):
        trims = []
        for iRoc in range(self.nROCs):
            rocTrims = [self.defaultTrim] * self.nPix
            trims.append({'ROC': iRoc, 'Trims': rocTrims})
        print "  -> created list of default trimbits(=%d) for %d ROCs"%(self.defaultTrim, self.nROCs)
        return trims

    # default TBM settings
    def getTbmParameters(self, ModuleID, options={}):
        tbmParameters = [
            {'Name': 'TBMABase0', 'Value': 0},
            {'Name': 'TBMBBase0', 'Value': 0},
            {'Name': 'TBMAAutoReset', 'Value': 0},
            {'Name': 'TBMBAutoReset', 'Value': 0},
            {'Name': 'TBMANoTokenPass', 'Value': 0},
            {'Name': 'TBMBNoTokenPass', 'Value': 0},
            {'Name': 'TBMADisablePKAMCounter', 'Value': 1},
            {'Name': 'TBMBDisablePKAMCounter', 'Value': 1},
            {'Name': 'TBMAPKAMCount', 'Value': 5},
            {'Name': 'TBMBPKAMCount', 'Value': 5},
            {'Name': 'TBMPLLDelay', 'Value': 52},
            {'Name': 'TBMADelay', 'Value': 100},
            {'Name': 'TBMBDelay', 'Value': 100},
        ]
        return tbmParameters

    # default mask bits, 0=unmasked, 1=masked
    def getMaskBits(self, ModuleID, options={}):
        masks = []
        for iRoc in range(self.nROCs):
            rocMasks = [self.defaultMask] * self.nPix
            masks.append({'ROC': iRoc, 'Masks': rocMasks})
        print "  -> created list of default maskbits(=%d) for %d ROCs"%(self.defaultMask, self.nROCs)
        return masks