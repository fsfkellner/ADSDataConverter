import os
import arcpy
import sys
sys.path.append(r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner')
# sys.path.append(r'C:\Data\ADSDataConverter')
import ADSFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\NRGG_Tools')
# sys.path.append(r'C:\Data')
import NRGG

topLevelADSFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R01\ADS\Archived\Yearly\WithFNF'
workingFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\ADS_For_RS_2020'
scratchWorkspace = arcpy.env.workspace

featureClasses = ADSFunctions.findAllFeatureClasses(topLevelADSFolder)
featureClasses = featureClasses[:-8]
for featureClass in featureClasses:
    print('working on', os.path.basename(featureClass))
    layerViewName = '{}_Copy'.format(os.path.basename(featureClass))
    year = ADSFunctions.findDigit(layerViewName)[1:]
    year = NRGG.listStringJoiner(year, '')

    GDBName = 'ADS_SingleDCAValue_Tables_{}'.format(year)

    outPutGDB = ADSFunctions.makeNewGDBIfDoesntExist(workingFolder, GDBName)
    arcpy.FeatureClassToFeatureClass_conversion(
        featureClass, scratchWorkspace, layerViewName)

    uniqueDCAValues = ADSFunctions.getAllUniqueDCAValues(
        layerViewName)

    ADSFunctions.setDamageToZero(layerViewName)
    ADSFunctions.makeCopyOfOriginalOBJECTID(layerViewName)

    uniqueDCAValues.remove(11006)
    for DCAValue in uniqueDCAValues:
        print('Working on', DCAValue)
        tableName = 'ADS_Expanded_{}_{}'.format(DCAValue, year)

        ADSFunctions.makeEmptyADSTable(tableName, outPutGDB)

        everyDCARecord = ADSFunctions.getEveryRecordForSingleDCAValue(
            layerViewName, DCAValue, scratchWorkspace)

        ADSFunctions.updateTablewithEveryDCARecord(
            tableName, everyDCARecord)

        ADSFunctions.mergeDuplicatesNoHost(tableName, outPutGDB)
