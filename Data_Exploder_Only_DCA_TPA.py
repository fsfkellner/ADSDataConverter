import os
import arcpy
import sys
# sys.path.append(r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner')
sys.path.append(r'C:\Data\ADSDataConverter')
import ADSFunctions

# sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\NRGG_Tools')
sys.path.append(r'C:\Data')
import NRGG

topLevelADSFolder = r'C:\Data\ADS_Data'
workingFolder = r'C:\Data\ADS_Testing'
scratchWorkspace = r'C:\Data\ADS_Testing\ScratchSpace.gdb'

featureClasses = ADSFunctions.findAllFeatureClasses(topLevelADSFolder)
featureClasses = featureClasses[-9:]

for featureClass in featureClasses:
    print('working on', os.path.basename(featureClass))
    layerViewName = '{}_Copy'.format(os.path.basename(featureClass))
    year = ADSFunctions.findDigits(layerViewName)[1:]
    year = NRGG.listStringJoiner(year, '')

    GDBName = 'ADS_SingleDCAValue_Tables_{}.gdb'.format(year)

    outPutGDB = ADSFunctions.makeNewGDBIfDoesntExist(workingFolder, GDBName)
    allValuesOutput = arcpy.CreateFeatureDataset_management(
        outPutGDB, 'allValueTables')[0]
    mergedTableOutput = arcpy.CreateFeatureDataset_management(
        outPutGDB, 'mergedTables')[0]
    mergedFeatureClassOutput = arcpy.CreateFeatureDataset_management(
        outPutGDB, 'mergedFeatureClasses')[0]

    arcpy.FeatureClassToFeatureClass_conversion(
        featureClass, scratchWorkspace, layerViewName)

    ADSFunctions.setDamageToZero(layerViewName)
    uniqueDCAValues = ADSFunctions.getAllUniqueDCAValues(
        layerViewName)

    ADSFunctions.makeCopyOfOriginalOBJECTID(layerViewName)

    uniqueDCAValues.remove(11006)
    uniqueDCAValues = [11015]
    for DCAValue in uniqueDCAValues:
        print('Working on', DCAValue)
        tableName = 'ADS_Expanded_{}_{}'.format(DCAValue, year)
        featureClassName = os.path.join(
            mergedFeatureClassOutput, 'ADS_{}_{}'.format(DCAValue, year))

        ADSFunctions.makeEmptyADSTable(tableName, allValuesOutput)

        everyDCARecord = ADSFunctions.getEveryRecordForSingleDCAValue(
            layerViewName, DCAValue, scratchWorkspace)

        ADSFunctions.updateTablewithEveryDCARecord(
            tableName, everyDCARecord)

        mergedTableName = ADSFunctions.mergeDuplicatesNoHost(
            tableName, mergedTableOutput)
        ids = ADSFunctions.returnAllValuesFromField(
            mergedTableName, 'ORIGINAL_ID')
        ids = NRGG.listStringJoiner(ids)
        ADSFunctions.selectPolygonsFromOriginalData(
            layerViewName, ids,
            featureClassName, mergedFeatureClassOutput)
        ADSFunctions.deleteUneededFields(featureClassName, ['ADS_OBJECTID'])
        arcpy.JoinField_management(
            featureClassName, 'ADS_OBJECTID', mergedTableName,
            'ORIGINAL_ID', 'ORIGINAL_ID;DUPLICATE;TPA;DCA_CODE;HOST;ACRES')
