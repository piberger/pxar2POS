#!/usr/bin/env python
import argparse
import ConfigParser
import os
import shutil

try:
    from pxar2POSConverter import pxar2POSConverter as pxar2POSConverter
except:
    print "\x1b[31mcould not load module: 'pxar2POSConverter', make sure the file exists.\x1b[0m"


print "-"*80
print '''
                                       2222       $$$$$$$\   $$$$$$\   $$$$$$\\
           ____  ____                 22  22     $$  __$$\ $$  __$$\ $$  __$$\\
          |_  _||_  _|                   22     $$ |  $$ |$$ /  $$ |$$ /  \__|
 _ .--.     \ \  / /    ,--.    _ .--. 222222  $$$$$$$  |$$ |  $$ |\$$$$$$
[ '/'`\ \    > `' <    `'_\ :  [ `/'`\]       $$  ____/ $$ |  $$ | \____$$\\
 | \__/ |  _/ /'`\ \_  // | |,  | |          $$ |      $$ |  $$ |$$\   $$ |
 | ;.__/  |____||____| `-;__/ [___]         $$ |       $$$$$$  |\$$$$$$  |
[__|                                        \__|       \______/  \______/
'''
try:
    import subprocess
    print "version:", subprocess.check_output(["git", "describe", "--always"]).replace('\n', '')
except:
    pass
print "-"*80

# create user configuration (= not under version control) - if not existing
if not os.path.isfile('UserConfiguration.ini'):
    if os.path.isfile('DefaultConfiguration.ini'):
        try:
            shutil.copy('DefaultConfiguration.ini', 'UserConfiguration.ini')
        except:
            print "\x1b[31mERROR: can't create UserConfiguration.ini file!\x1b[0m"
    else:
        print "\x1b[31mERROR: can't find DefaultConfiguration.ini file!\x1b[0m"

# load default configuration first and then overwrite with user configuration
config = ConfigParser.SafeConfigParser()
try:
    config.read('DefaultConfiguration.ini')
except:
    print "\x1b[31mERROR: can't load DefaultConfiguration.ini file!\x1b[0m"
try:
    config.read('UserConfiguration.ini')
except:
    print "\x1b[31mERROR: can't load UserConfiguration.ini file!\x1b[0m"


# read arguments from command line
parser = argparse.ArgumentParser(description='converter for pxar data from database to pixel online software (POS) format, see README.md for some general examples how to use it')

parser.add_argument('-m','--module',dest='module',
                     help='module ID, e.g. M1234 or list of modules separated by comma, e.g. M1234,M2345,M3456',
                     default='')
parser.add_argument('-T', '--trim', dest='trim',
                    help='trim value, e.g. 35',
                    default=config.get('Global', 'DefaultTrim'))
parser.add_argument('-t', '--temp', dest='temp',
                    help='temperature',
                    default=config.get('Global', 'DefaultTemperature'))
parser.add_argument('-o', '--output', dest='output',
                    help='output folder',
                    default=config.get('Paths', 'Output'))
parser.add_argument('-p', '--positions', dest='positions',
                    help='module positions file',
                    default=config.get('Paths', 'ModuleList'))
parser.add_argument('-s', '--source', dest='source',
                    help='data source. default: pisa DB, database url (http://...), local path to Fulltest folders, \'default\' to have pXar default configuration....',
                    default=config.get('Global', 'Database'))
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help='verbose output',
                    default=config.get('Global', 'Verbose') == 1)

args = parser.parse_args()

if len(args.module.strip()) < 1:
    print "no module specified. show help with -h"
    exit(0)

# show summary of parameters
print "  -> module:", args.module
print "  -> trim:", args.trim
print "  -> temperature:", args.temp
print "  -> module positions from:", args.positions
print "  -> module data from:", args.source
print "  -> save data in:", args.output
if args.verbose:
    print "    -> verbose output is turned ON"

# initialize converter
print "initialize converter..."
converter = pxar2POSConverter(
    options={
        'ModulePositionTable': args.positions,
        'DataSource': args.source,
        'OutputPath': args.output,
        'verbose': args.verbose,
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

