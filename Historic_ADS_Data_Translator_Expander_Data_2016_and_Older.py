# This script is the first step in processing ADS data to facilitate long term ADS analysis
# across many years of ADS data for processes such as unioning DCA files together 
# This script is designed to only work with historic ADS data which are those 
# that are 2016 and older 
# and Example of these types of data are those housed in 
# T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R01\ADS\Archived\Yearly for Region 1 
# and 
# T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R4_Historic_ADS_Data for Region 4
# The script "Expands" the ADS data by taking DCA1, DCA2, DCA3 and making new tables of data 
# where each table has only one type of DCA value and each DCA value has its own row in the table
# The output of this script is something like the data found in 
# T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\Expanded_Data\R1_Expanded_ADS_Tables
# The fields that are kept when this data is "expanded" and translated are
# TPA, DCA_CODE, HOST_CODE, DAMAGE_TYPE_CODE, and ACRES
# if in the future you wanted to keep this translation process but 
# change the fields that are included or not included in this data translation 
# the you would just need to make changes to the 
# ADSFunctions.makeEmptyADSTable()
# and 
# ADSFunctions.updateTablewithEveryDCARecord()
# Functions
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
topLevelADSFolder = # Exampe: r'T:\FS\NFS\R01\Program\3400ForestHealthProtection'
# a folder where output GDBs will be written to
workingFolder = # Example : r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\Expanded_Data\R1_Expanded_ADS_Tables'
# Create an empty GDB and provide a path to this 
scratchWorkspace = # Example: r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\WorkingFolder\NewTemp.gdb'
region = 'R1' # This is needed for naming convetions
#############################################

featureClasses = ADSFunctions.findAllFeatureClasses(
    topLevelADSFolder, 'Damage')

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
