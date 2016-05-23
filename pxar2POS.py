#!/usr/bin/env python

from CalibrationDataProvider.LocalData import CalibrationDataProvider
from ModulePositionProvider.LocalData import ModulePositionProvider
from POSWriter.POSWriter import POSWriter

dataSource = CalibrationDataProvider(dataPath="D:/ModuleData/")
modulePositionTable = ModulePositionProvider(dataPath="D:/ModuleData/")
posWriter = POSWriter(outputPath="D:/ModuleData/")


moduleID = 'M2222'
modulePosition = modulePositionTable.getModulePosition(moduleID)
rocDACs = dataSource.getRocDacs(ModuleID = moduleID, options = {'Test': '*ulltest*_m20', 'DacSuffix': '35'})
posWriter.writeDACs(moduleID, modulePosition, rocDACs)
