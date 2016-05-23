class AbstractCalibrationDataProvider(object):

    def getRocDacs(self, ModuleID, options = {}):
        raise NotImplementedError('getRocDacs() not implemented!')

    def getTrimBits(self, ModuleID, options = {}):
        raise NotImplementedError('getTrimBits() not implemented!')

    def getTbmParameters(self, ModuleID, options={}):
        raise NotImplementedError('getTbmParameters() not implemented!')
