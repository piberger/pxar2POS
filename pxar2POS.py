#!/usr/bin/env python

from CalibrationDataProvider.LocalData import CalibrationDataProvider
from ModulePositionProvider.LocalData import ModulePositionProvider
from POSWriter.POSWriter import POSWriter

dataSource = CalibrationDataProvider(dataPath="D:/ModuleData/")
modulePositionTable = ModulePositionProvider(dataPath="D:/ModuleData/")
posWriter = POSWriter(outputPath="D:/ModuleData/")


moduleID = 'M2222'

# get module position in detector
modulePosition = modulePositionTable.getModulePosition(moduleID)

# read module calibration parameters
rocDACs = dataSource.getRocDacs(ModuleID = moduleID, options = {'Test': '*ulltest*_m20', 'DacSuffix': '35'})
rocTrimbits = dataSource.getTrimBits(ModuleID = moduleID, options = {'Test': '*ulltest*_m20', 'TrimSuffix': '35'})

# write to pixel online software output format
posWriter.writeDACs(moduleID, modulePosition, rocDACs)
posWriter.writeTrim(moduleID, modulePosition, rocTrimbits)
