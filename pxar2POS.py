#!/usr/bin/env python

from CalibrationDataProvider.PisaDB import CalibrationDataProvider
from ModulePositionProvider.LocalData import ModulePositionProvider
from POSWriter.POSWriter import POSWriter

dataSource = CalibrationDataProvider(dataPath="D:/ModuleData/")
modulePositionTable = ModulePositionProvider(dataPath="D:/ModuleData/")
posWriter = POSWriter(outputPath="D:/ModuleData/")


moduleID = 'M2222'

# get module position in detector
modulePosition = modulePositionTable.getModulePosition(moduleID)

# read dacs and output POS files
rocDACs = dataSource.getRocDacs(ModuleID = moduleID, options = {'Test': '*ulltest*_m20', 'TrimValue': '35'})
posWriter.writeDACs(moduleID, modulePosition, rocDACs)

# trimbits
rocTrimbits = dataSource.getTrimBits(ModuleID = moduleID, options = {'Test': '*ulltest*_m20', 'TrimValue': '35'})
posWriter.writeTrim(moduleID, modulePosition, rocTrimbits)
