#!/usr/bin/env python
import argparse
import ConfigParser
import os
import shutil
import glob

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

# ----------------------------------------------------------------------------------------------------------------
#  configuration
# ----------------------------------------------------------------------------------------------------------------

configurationId = config.get('Global', 'ConfigurationId')
configurationBase = config.get('Paths', 'Output')
moduleList = config.get('Paths', 'ModuleList')

detectorSections = ['BpO','BmO','BpI','BmI']
detectorLayerLadders = [6, 14, 22, 32]
detectorModules = 4

detectorModuleNameFormat = 'BPix_{Section}{insideOutside}_SEC*_LYR{Layer}_LDR{Ladder}{ModuleType}_MOD{Module}'

checks = [
    ['DACs', '/dac/{configurationId}/ROC_DAC_module_{detectorModuleName}.dat'],
    ['Readback', '/iana/{configurationId}/ROC_Iana_{detectorModuleName}.dat'],
    ['Mask', '/mask/{configurationId}/ROC_Masks_module_{detectorModuleName}.dat'],
    ['TBM', '/tbm/{configurationId}/TBM_module_{detectorModuleName}.dat'],
    ['trim', '/trim/{configurationId}/ROC_Trims_module_{detectorModuleName}.dat'],
]

# ----------------------------------------------------------------------------------------------------------------
#  run the checks
# ----------------------------------------------------------------------------------------------------------------

problems = {}

for layer, detectorLayerLadder in enumerate(detectorLayerLadders, start=1):
    print "\x1b[32m -> layer %d\x1b[0m"%layer

    for insideOutside in ['O', 'I']:
        print "\x1b[32m halfshell %s\x1b[0m" % insideOutside

        for ladder in range(1, detectorLayerLadder+1):

            ladderString = '%2d:'%ladder
            for section,modules in [['Bm',[4,3,2,1]],['Bp',[1,2,3,4]]]:
                for module in modules:

                    if layer == 1:
                        moduleTypes = ['H', 'F']
                    else:
                        moduleTypes = ['F']

                    for moduleType in moduleTypes:
                        detectorModuleName = detectorModuleNameFormat.format(
                            Section=section,
                            insideOutside=insideOutside,
                            Ladder=ladder,
                            Layer=layer,
                            Module=module,
                            ModuleType=moduleType,
                        )

                        for checkName,checkPaths in checks:
                            globPath = configurationBase + checkPaths.format(
                                configurationId=configurationId,
                                detectorModuleName=detectorModuleName,
                            )
                            globFiles = glob.glob(globPath)

                            if len(globFiles) != 1:
                                ladderString += 'X'
                                if detectorModuleName not in problems:
                                    problems[detectorModuleName] = []
                                problems[detectorModuleName].append(checkName)
                            else:
                                ladderString += '.'

                    ladderString += ' '
            print ladderString

print "problematic modules:"
for problem in problems.iteritems():
    print problem