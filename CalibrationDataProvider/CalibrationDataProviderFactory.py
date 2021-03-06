from PisaDB import CalibrationDataProvider as PisaDBCalibrationDataProvider
from PisaDBparametersForBBTest import CalibrationDataProvider as PisaDBforBBCalibrationDataProvider
from LocalData import CalibrationDataProvider as LocalCalibrationDataProvider
from DefaultValues import CalibrationDataProvider as DefaultCalibrationDataProvider

class CalibrationDataProviderFactory(object):

    def __init__(self):
        pass

    def init(self, dataSource, verbose=False):
        if ('http://' in dataSource and 'BBTEST:' in dataSource):
            print "  -> selected data source: MySQL database / \x1b[33mBB test parameters\x1b[0m"
            return PisaDBforBBCalibrationDataProvider(dataSource=dataSource.replace('BBTEST:',''), verbose=verbose)
        elif 'http://' in dataSource:
            # connect to Pisa DB
            print "  -> selected data source: MySQL database"
            return PisaDBCalibrationDataProvider(dataSource=dataSource, verbose=verbose)
        elif dataSource.lower() == 'default':
            # just default values
            print "  -> selected data source: default values"
            return DefaultCalibrationDataProvider(dataSource=dataSource, verbose=verbose)
        else:
            # or fetch data locally
            print "  -> selected data source: local pXar test folders"
            return LocalCalibrationDataProvider(dataSource=dataSource, verbose=verbose)
