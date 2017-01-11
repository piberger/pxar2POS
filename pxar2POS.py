#!/usr/bin/env python
import argparse
import ConfigParser
import os
import shutil
import glob
import fnmatch
from POSWriter.POSWriter import POSWriter

try:
    from pxar2POSConverter import pxar2POSConverter as pxar2POSConverter
except:
    print "\x1b[31mcould not load module: 'pxar2POSConverter', make sure the file exists.\x1b[0m"


# show splash screen
print "-"*80
print '''
                                        222       $$$$$$$\   $$$$$$\   $$$$$$\\
           ____  ____                  2  22     $$  __$$\ $$  __$$\ $$  __$$\\
          |_  _||_  _|                   22     $$ |  $$ |$$ /  $$ |$$ /  \__|
 _ .--.     \ \  / /    ,--.    _ .--. 22222   $$$$$$$  |$$ |  $$ |\$$$$$$
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
parser.add_argument('-i', '--configuration-id', dest='configuration_id',
                    help='configuration ID',
                    default=config.get('Global', 'ConfigurationId'))
parser.add_argument('-d', '--do', dest='do',
                    help='command to run',
                    default='')
args = parser.parse_args()

# check given options, --do can not be used with -m at the same time
if len(args.module.strip()) < 1 and len(args.do) < 1:
    print "no module specified. show help with -h"
    exit(0)
elif len(args.do) > 0 and len(args.module) > 0:
    print "running commands for certain modules only is not implemented yet, omit -m option to run it for all!"
    exit(0)
elif len(args.do) > 0:

    # --do needs a config ID specified
    configurationID = -1
    try:
        configurationID = int(args.configuration_id)
        if configurationID < 0:
            raise Exception("no configuration ID specified!")
    except:
        print "to run a command, please specify configuration ID with -i or in UserConfiguration.ini"
        exit(0)

    # find next free config ID
    posWriter = POSWriter(outputPath=args.output, configurationID=configurationID)
    inputFileNames = posWriter.getOutputFileNames()
    configurations = []
    for dataType, dataSubfolder in inputFileNames.items():
        outputFolder = '/'.join(dataSubfolder.split('/')[:-2])
        globPath = args.output + '/' + outputFolder + '/*/'
        configurations += [int(x.strip('/').split('/')[-1]) for x in glob.glob(globPath)]
    newConfigurationID = max(configurations) + 1

    runCommands = [x.strip().split(':') for x in args.do.split(';')]

    # ask user confirmation
    print '+%s+'%('-'*78)
    print '|%s|'%((' copy configuration ID %d -> %d ?'%(configurationID, newConfigurationID)).ljust(78))
    print '|%s|'%(' '*78)
    print '|%s|'%((' and run the following commands on config ID %d:'%newConfigurationID).ljust(78))
    for runCommand in runCommands:
        print '| %s|'%(('%r'%runCommand).ljust(77))
    print '|%s|'%(' '*78)
    print '+%s+'%('-'*78)
    answer = raw_input('ENTER/y to continue, q to quit>')

    if answer.lower() == 'y' or len(answer.strip()) < 1:

        # copy configuration to new ID
        posWriterOutput = POSWriter(outputPath=args.output, configurationID=newConfigurationID, createFoldersOnInitialization=False)
        outputFileNames = posWriterOutput.getOutputFileNames()
        print "copy configuration..."
        for dataType, dataSubfolder in inputFileNames.items():
            copyFrom = args.output + '/' + '/'.join(dataSubfolder.split('/')[:-1])
            copyTo = args.output + '/' + '/'.join(outputFileNames[dataType].split('/')[:-1])
            if args.verbose:
                print "copy:", copyFrom, " --> ", copyTo
            shutil.copytree(copyFrom, copyTo)
        print "  -> done."

        # run commands
        print "run commands..."

        #  examples: enable PKAM counter, but only for L4 modules: tbm:*_LYR4_*?set:TBMADisablePKAMCounter:0
        #    dac:set:Vdd:8
        #    dac:incr8bit:Vana:20
        #    dac:incr4bit:Vdd:1
        #    tbm:and:TBMADelay:128

        # loop over list of commands separated by ';'
        for runCommand in runCommands:
            conditional = ''

            # check if directory (first argument) exists
            if runCommand[0] in outputFileNames:

                # extract condition and instruction
                if args.verbose:
                    print "found! ", outputFileNames[runCommand[0]]
                if '?' in runCommand[1]:
                    conditional = runCommand[1].split('?')[0]
                    instruction = runCommand[1].split('?')[1].lower()
                else:
                    instruction = runCommand[1].lower()

                # loop over ALL files
                datFileNamesMask = args.output + '/' + outputFileNames[runCommand[0]].format(Position='*')
                datFileNames = glob.glob(datFileNamesMask)
                for datFileName in datFileNames:
                    conditionalMet = False
                    if len(conditional) < 1:
                        conditionalMet = True
                    if args.verbose:
                        print datFileName
                    with open(datFileName, 'r') as datFile:
                        datFileLines = datFile.readlines()

                    # loop over all lines of the dat file
                    changesMade = False
                    for i in range(len(datFileLines)):
                        if conditionalMet:
                            lineParts = [x.strip() for x in datFileLines[i].split(':')]

                            if instruction == 'set':
                                if lineParts[0] == runCommand[2]:
                                    lineParts[1] = runCommand[3]
                                    datFileLines[i] = ': '.join(lineParts) + '\n'

                                    # reset condition and mark the file as changed
                                    if len(conditional) > 0:
                                        conditionalMet = False
                                    changesMade = True
                            elif instruction == 'and':
                                if lineParts[0] == runCommand[2]:
                                    lineParts[1] = '%d'%(int(lineParts[1]) & int(runCommand[3]))
                                    datFileLines[i] = ': '.join(lineParts) + '\n'

                                    # reset condition and mark the file as changed
                                    if len(conditional) > 0:
                                        conditionalMet = False
                                    changesMade = True
                            elif instruction == 'or':
                                if lineParts[0] == runCommand[2]:
                                    lineParts[1] = '%d'%(int(lineParts[1]) | int(runCommand[3]))
                                    datFileLines[i] = ': '.join(lineParts) + '\n'

                                    # reset condition and mark the file as changed
                                    if len(conditional) > 0:
                                        conditionalMet = False
                                    changesMade = True
                            elif instruction.startswith('incr') and (instruction.endswith('bit') or instruction.endswith('bits')):
                                nBits = int(instruction.replace('bits','').replace('bit','').replace('incr',''))
                                if nBits < 1:
                                    print "\x1b[31mERROR: incr#bit operator needs # >= 1! defaulting to 8 bit!\x1b[0m"
                                    nBits = 8

                                if lineParts[0] == runCommand[2]:
                                    value = int(lineParts[1]) + int(runCommand[3])
                                    if value > (2**nBits)-1:
                                        value = (2**nBits)-1
                                    elif value < 0:
                                        value = 0
                                    lineParts[1] = '%d'%(value)
                                    datFileLines[i] = ': '.join(lineParts) + '\n'

                                    # reset condition and mark the file as changed
                                    if len(conditional) > 0:
                                        conditionalMet = False
                                    changesMade = True

                        else:
                            # check if condition is fulfilled
                            if fnmatch.fnmatch(datFileLines[i].strip(), conditional):
                                if args.verbose:
                                    print "    -> condition met:", datFileLines[i], conditional
                                conditionalMet = True

                    # write file back, if changes were made
                    if changesMade:
                        if args.verbose:
                            print "update file: '\x1b[34m{datFileName}\x1b[0m'".format(datFileName=datFileName)
                        with open(datFileName, 'w') as datFile:
                            datFile.writelines(datFileLines)

            elif runCommand[0] == 'exit':
                break
            else:
                print "\x1b[31mERROR: command type not found:",runCommand[0],"\x1b[0m"

        print "  -> done."

        print " -> done."

    else:
        print " \x1b[31m-> aborted!\x1b[0m"

else:
    # obtain data from DB

    # show summary of parameters
    if args.configuration_id < 0:
        print "  -> NO configuration id specified (with -i), saving all files directly into the output folder"
    else:
        print "  -> configuration ID: ", args.configuration_id
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
            'Verbose': args.verbose,
            'ConfigurationID': args.configuration_id,
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

