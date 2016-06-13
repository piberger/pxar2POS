#!/usr/bin/env python
import argparse
from pxar2POSConverter import pxar2POSConverter as pxar2POSConverter

# initialize converter
options = {
    'ModulePositionTable': 'ExampleData/modules.txt',
    'DataSource': 'http://cmspixelprod.pi.infn.it',  # if it contains http://, it will be interpreted as url to sql server, otherwise as a local path
    'OutputPath': 'OutputData'
}
print "-"*80
print " initialize pxar -> POS converter:"
print "-"*80
print "  -> module positions from ", options['ModulePositionTable']
print "  -> module data from ", options['DataSource']
print "  -> save data in ", options['OutputPath']

converter = pxar2POSConverter(options=options)

# read arguments from command line
parser = argparse.ArgumentParser(description='converter for pxar data from database to pixel online software')
parser.add_argument('-m','--module',dest='module',
                     help='module ID, e.g. M1234',
                     default='M2222')
parser.add_argument('-T', '--trim', dest='trim',
                    help='trim value, e.g. 35',
                    default='35')
args = parser.parse_args()


# select which Fulltest of FullQualification to use
testOptions = {'Test': '*ulltest*_m20', 'TrimValue': args.trim}

# convert files
converter.convertModuleData(moduleID=args.module, testOptions=testOptions)

