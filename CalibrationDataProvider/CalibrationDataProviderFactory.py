from PisaDB import CalibrationDataProvider as PisaDBCalibrationDataProvider
from LocalData import CalibrationDataProvider as LocalCalibrationDataProvider
from DefaultValues import CalibrationDataProvider as DefaultCalibrationDataProvider

class CalibrationDataProviderFactory(object):

    def __init__(self):
        pass

    def init(self, dataSource):
        if 'http://' in dataSource:
            # connect to Pisa DB
            print "  -> selected data source: MySQL database"
            return PisaDBCalibrationDataProvider(dataSource=dataSource)
        elif dataSource.lower() == 'default':
            # just default values
            print "  -> selected data source: default values"
            return DefaultCalibrationDataProvider(dataSource=dataSource)
        else:
            # or fetch data locally
            print "  -> selected data source: local pXar test folders"
            return LocalCalibrationDataProvider(dataSource=dataSource)