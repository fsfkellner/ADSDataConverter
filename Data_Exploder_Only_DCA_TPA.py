########### Import statements ####################
import os
import arcpy
import sys
#sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
sys.path.append(r'C:\Data\ADSDataConverter')

import ADSFunctions

#sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
sys.path.append(r'C:\Data\NRGG')
import NRGG
###########################################################

################## variables that will need to be set by end user #################################
# folder in which the ADS data is contained 
# when putting in file paths in Python best practice is to start with a r and enclose path in "" or ''
# Exampe r'C:\Path\To\Data'

topLevelADSFolder = r'C:\Data\ADS_Data'
# a folder where output GDBs will be written to
workingFolder = r'C:\Data\ADS_Data'
# Create an empty GDB and provide a path to this 
scratchWorkspace = r'C:\Data\ADS_Data\Skratch.gdb'
#############################################

featureClasses = ADSFunctions.findAllFeatureClasses(
    topLevelADSFolder, 'Damage')
##### may need to experiement with the values in this next line to adjust what files analysis are calculated on
#featureClasses = featureClasses[1:-5] 


############## execution code, no need to change any of this code #################################
for featureClass in featureClasses:
    print('working on', os.path.basename(featureClass))
    layerViewName = '{}_Copy'.format(os.path.basename(featureClass))
    year = ADSFunctions.findDigits(layerViewName)[1:]
    year = NRGG.listStringJoiner(year, '')

    GDBName = 'ADS_SingleDCAValue_Tables_{}.gdb'.format(year)

    outPutGDB = ADSFunctions.makeNewGDBIfDoesntExist(workingFolder, GDBName)

    arcpy.FeatureClassToFeatureClass_conversion(
        featureClass, scratchWorkspace, layerViewName)

    ADSFunctions.setDamageToZero(layerViewName)
    uniqueDCAValues = ADSFunctions.getAllUniqueDCAValues(
        layerViewName)

    uniqueDCAValues = [int(DCAValue) for DCAValue in uniqueDCAValues]

    ADSFunctions.makeCopyOfOriginalOBJECTID(layerViewName)

    for DCAValue in uniqueDCAValues:
        print('Working on', DCAValue)
        tableName = 'ADS_Expanded_{}_{}'.format(DCAValue, year)
        featureClassName = 'ADS_{}_{}'.format(DCAValue, year)

        ADSFunctions.makeEmptyADSTable(tableName, outPutGDB)

        everyDCARecord = ADSFunctions.getEveryRecordForSingleDCAValue(
            layerViewName, DCAValue, scratchWorkspace)

        ADSFunctions.updateTablewithEveryDCARecord(
            tableName, everyDCARecord)

        mergedTableName = ADSFunctions.mergeDuplicatesNoHost(
            tableName, outPutGDB)
        ids = ADSFunctions.returnAllValuesFromField(
            mergedTableName, 'ORIGINAL_ID')
        ids = NRGG.listStringJoiner(ids)
        ADSFunctions.selectPolygonsFromOriginalData(
            layerViewName, ids,
            featureClassName, outPutGDB)
        ADSFunctions.deleteUneededFields(featureClassName, ['ADS_OBJECTID'])
        arcpy.JoinField_management(
            featureClassName, 'ADS_OBJECTID', mergedTableName,
            'ORIGINAL_ID', 'ORIGINAL_ID;DUPLICATE;TPA;DCA_CODE;HOST;ACRES')
