########### Import statements ####################
import os
import arcpy
import sys

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions
###########################################################

################## variables that will need to be set by end user #################################
# folder in which the ADS data is contained 
# when putting in file paths in Python best practice is to start with a r and enclose path in "" or ''
# Exampe r'C:\Path\To\Data'

topLevelADSFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\WorkingFolder\Merge_2015.gdb'
# a folder where output GDBs will be written to
workingFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R1_Expanded_ADS_Tables'
# Create an empty GDB and provide a path to this 
scratchWorkspace = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\WorkingFolder\NewTemp.gdb'
region = 'R1'
#############################################

featureClasses = ADSFunctions.findAllFeatureClasses(
    topLevelADSFolder, 'Damage')

featureClasses = featureClasses[-13:-12]

############## execution code, no need to change any of this code #################################
for featureClass in featureClasses:
    print('working on', os.path.basename(featureClass))
    layerViewName = '{}_Copy'.format(os.path.basename(featureClass))
    year = ADSFunctions.findDigits(layerViewName)[1:]
    year = NRGG.listStringJoiner(year, '')

    GDBName = '{}ADS_SingleDCAValue_Tables_{}.gdb'.format(region, year)

    outPutGDB = ADSFunctions.makeNewGDBIfDoesntExist(workingFolder, GDBName)

    arcpy.FeatureClassToFeatureClass_conversion(
        featureClass, outPutGDB, layerViewName)

    uniqueDCAValues = ADSFunctions.getAllUniqueDCAValues(layerViewName)
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
