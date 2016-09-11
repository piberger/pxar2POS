#!/usr/bin/env python
import argparse
from pxar2POSConverter import pxar2POSConverter as pxar2POSConverter


print "-"*80
print " pxar -> POS converter:"
print "-"*80

# read arguments from command line
parser = argparse.ArgumentParser(description='converter for pxar data from database to pixel online software')
parser.add_argument('-m','--module',dest='module',
                     help='module ID, e.g. M1234',
                     default='M2222')
parser.add_argument('-T', '--trim', dest='trim',
                    help='trim value, e.g. 35',
                    default='35')
parser.add_argument('-t', '--temp', dest='temp',
                    help='temperature',
                    default='-20')
parser.add_argument('-o', '--output', dest='output',
                    help='output folder',
                    default='OutputData')
parser.add_argument('-p', '--positions', dest='positions',
                    help='module positions file',
                    default='ExampleData/modules.txt')
parser.add_argument('-u', '--url', dest='url',
                    help='url to database',
                    default='http://cmspixelprod.pi.infn.it')



args = parser.parse_args()

print "  -> module:", args.module
print "  -> trim:", args.trim
print "  -> temperature:", args.temp
print "  -> module positions from:", args.positions
print "  -> module data from:", args.url
print "  -> save data in:", args.output

# initialize converter
print "initialize converter..."
options = {
    'ModulePositionTable': args.positions,
    'DataSource': args.url,  # if it contains http://, it will be interpreted as url to sql server, otherwise as a local path
    'OutputPath': args.output
}
converter = pxar2POSConverter(options=options)

# select which Fulltest of FullQualification to use
testOptions = {'Test': '*ulltest*_m20', 'TrimValue': args.trim}

# convert files
converter.convertModuleData(moduleID=args.module, testOptions=testOptions)

