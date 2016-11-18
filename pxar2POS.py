#!/usr/bin/env python
import argparse

try:
    from pxar2POSConverter import pxar2POSConverter as pxar2POSConverter
except:
    try:
        from pxar2PosConverter import pxar2POSConverter as pxar2POSConverter
    except:
        print "\x1b[31mcould not load module: 'pxar2POSConverter'\x1b[0m"


print "-"*80
print " pxar -> POS converter:"
print "-"*80

# read arguments from command line
parser = argparse.ArgumentParser(description='converter for pxar data from database to pixel online software (POS) format, see README.md for some general examples how to use it')

parser.add_argument('-m','--module',dest='module',
                     help='module ID, e.g. M1234 or list of modules separated by comma, e.g. M1234,M2345,M3456',
                     default='M9999')
parser.add_argument('-T', '--trim', dest='trim',
                    help='trim value, e.g. 35',
                    default='35')
parser.add_argument('-t', '--temp', dest='temp',
                    help='temperature',
                    default='m20')
parser.add_argument('-o', '--output', dest='output',
                    help='output folder',
                    default='OutputData')
parser.add_argument('-p', '--positions', dest='positions',
                    help='module positions file',
                    default='ExampleData/modules.txt')
parser.add_argument('-s', '--source', dest='source',
                    help='data source. default: pisa DB, database url (http://...), local path to Fulltest folders, \'default\' to have pXar default configuration....',
                    default='http://cmspixelprod.pi.infn.it')

args = parser.parse_args()

print "  -> module:", args.module
print "  -> trim:", args.trim
print "  -> temperature:", args.temp
print "  -> module positions from:", args.positions
print "  -> module data from:", args.source
print "  -> save data in:", args.output

# initialize converter
print "initialize converter..."
converter = pxar2POSConverter(
    options={
        'ModulePositionTable': args.positions,
        'DataSource': args.source,
        'OutputPath': args.output
    }
)

# select which Fulltest of FullQualification to use
testOptions = {'Test': '*ulltest*_' + args.temp, 'tempnominal': args.temp, 'TrimValue': args.trim}

# convert files
moduleIDList = args.module.replace(';',',').split(',')
for moduleID in moduleIDList:
    print '*'*40
    print '  %s:'%moduleID
    print '*'*40
    converter.convertModuleData(moduleID=moduleID, testOptions=testOptions)

