########### Import statements ####################
import os
import arcpy
import sys
sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG
###########################################################

################## variables that will need to be set by end user #################################
# folder in which the ADS data is contained 
# when putting in file paths in Python best practice is to start with a r and enclose path in "" or ''
# Exampe r'C:\Path\To\Data'

topLevelADSFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R01\ADS\Archived\Yearly'
# a folder where output GDBs will be written to
workingFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\ADS_RS_2020'
# Create an empty GDB and provide a path to this 
scratchWorkspace = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\WorkingFolder\LastTemp.gdb'
#############################################

featureClasses = ADSFunctions.findAllFeatureClasses(topLevelADSFolder)
##### may need to experiement with the values in this next line to adjust what files analysis are calculated on
featureClasses = featureClasses[1:-5] 

featureClasses = [r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R01\ADS\Archived\Yearly\WithFNF\1999\R1ADS1999.gdb\R1ADS1999Damage']

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
    #uniqueDCAValues = ADSFunctions.getAllUniqueDCAValues(
    #    layerViewName)
    #uniqueDCAValues = [int(DCAValue) for DCAValue in uniqueDCAValues]
    uniqueDCAValues = [11006]
    #uniqueDCAValues.remove(11006)

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
