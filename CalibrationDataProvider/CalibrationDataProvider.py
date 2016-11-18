class AbstractCalibrationDataProvider(object):

    def __init__(self):
        # module/chip properties
        self.nROCs = 16
        self.nRows = 80
        self.nCols = 52
        self.nPix = self.nRows * self.nCols

        # default trim bit value. 0=lowest threshold, 15=highest threshold
        self.defaultTrim = 15
        self.defaultMask = 0

    def getRocDacs(self, ModuleID, options = {}):
        raise NotImplementedError('getRocDacs() not implemented!')

    def getTrimBits(self, ModuleID, options = {}):
        raise NotImplementedError('getTrimBits() not implemented!')

    def getTbmParameters(self, ModuleID, options={}):
        raise NotImplementedError('getTbmParameters() not implemented!')

    def getMaskBits(self, ModuleID, options = {}):
        raise NotImplementedError('getMaskBits() not implemented!')
