#!/usr/bin/env python

from pxar2POSConverter import pxar2POSConverter as pxar2POSConverter

# initialize converter
converter = pxar2POSConverter()

# ModuleID
moduleID = 'M2222'

# select which Fulltest of FullQualification to use
testOptions = {'Test': '*ulltest*_m20', 'TrimValue': '35'}

converter.convertModuleData(moduleID=moduleID, testOptions=testOptions)

