import os
from collections import Counter
import arcpy
import sys
# sys.path.append(r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner')
sys.path.append(r'C:\Data\ADSDataConverter')
import DataExplorerFunctions

# sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\NRGG_Tools')
sys.path.append(r'C:\Data')
import NRGG

outPutGDB = r'C:\Data\Testing_ADS.gdb'
scratchWorkspace = arcpy.env.workspace


fc = r'C:\Data\R1ADS1999.gdb\R1ADS1999Damage'
layerViewName = '{}_Copy'.format(os.path.basename(fc))

arcpy.FeatureClassToFeatureClass_conversion(
    fc, scratchWorkspace, layerViewName)

uniqueDCAValues = DataExplorerFunctions.getAllUniqueDCAValues(
    layerViewName)

DataExplorerFunctions.setDamageToZero(layerViewName)

DataExplorerFunctions.makeCopyOfOriginalOBJECTID(layerViewName)

year = DataExplorerFunctions.findDigit(layerViewName)[1:]
year = NRGG.listStringJoiner(year, '')

for DCAValue in uniqueDCAValues:

    tableName = 'ADS_Expanded_{}'.format(DCAValue)

    DataExplorerFunctions.makeEmptyADSTable(tableName, outPutGDB)

    everyDCARecord = DataExplorerFunctions.getEveryRecordForDCAValue(
        layerViewName, DCAValue, scratchWorkspace)

    DataExplorerFunctions.updateTablewithEveryDCARecord(
        tableName, everyDCARecord)