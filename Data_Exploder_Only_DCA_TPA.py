import os
import arcpy
import sys
# sys.path.append(r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner')
sys.path.append(r'C:\Data\ADSDataConverter')
import ADSFunctions

# sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\NRGG_Tools')
sys.path.append(r'C:\Data')
import NRGG

outPutGDB = r'C:\Data\Testing_ADS.gdb'
scratchWorkspace = arcpy.env.workspace


fc = r'C:\Data\R1ADS1999.gdb\R1ADS1999Damage'
layerViewName = '{}_Copy'.format(os.path.basename(fc))

arcpy.FeatureClassToFeatureClass_conversion(
    fc, scratchWorkspace, layerViewName)

uniqueDCAValues = ADSFunctions.getAllUniqueDCAValues(
    layerViewName)

ADSFunctions.setDamageToZero(layerViewName)

ADSFunctions.makeCopyOfOriginalOBJECTID(layerViewName)

year = ADSFunctions.findDigit(layerViewName)[1:]
year = NRGG.listStringJoiner(year, '')

uniqueDCAValues.remove(11006)
for DCAValue in uniqueDCAValues:
    tableName = 'ADS_Expanded_{}_{}'.format(DCAValue, year)

    ADSFunctions.makeEmptyADSTable(tableName, outPutGDB)

    everyDCARecord = ADSFunctions.getEveryRecordForSingleDCAValue(
        layerViewName, DCAValue, scratchWorkspace)

    ADSFunctions.updateTablewithEveryDCARecord(
        tableName, everyDCARecord)
    
    ADSFunctions.mergeDuplicatesNoHost(tableName, outPutGDB)
