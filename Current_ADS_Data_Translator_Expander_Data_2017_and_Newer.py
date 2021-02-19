# This script is the first step in taking current ADS data 
# those 2017 and newer and preparing them so they can easily 
# be used inconjunction with 2016 and older historic ADS data
# for long term analyisis such as unioning
# the script pulls out single DCA values from the feature class
# and creates a table containing records for only one DCA value
# The fields that are retained during this translation are
# Severity_Class, SeverityWeightedAcres, MidPoint, HOST_CDOE and DAMAGE_TYPE_CODE
#####################################################################################
import arcpy
import os

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions

###################### Input Variables ##################################
featureClass = #Example : r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R01\ADS\Archived\Yearly\WithFNF\2020\R1R4_ADS_2020_FinalDatsets.gdb\R1ADS2020Damage'
year = 2020

outputGDB = # Example : r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\Expanded_Data\R1_Expanded_ADS_Tables\R1ADS_SingleDCAValue_Tables_2020.gdb'
###########################################################################

copyName = '{}_copy'.format(os.path.basename(featureClass))
arcpy.FeatureClassToFeatureClass_conversion(featureClass, outputGDB, copyName)

ADSFunctions.makeCopyOfOriginalOBJECTID('{}_copy'.format(os.path.basename(featureClass)))
tableName = '{}_TableView'.format(os.path.basename(featureClass))
arcpy.MakeTableView_management(os.path.join(outputGDB, copyName), tableName)

DCAValues = NRGG.uniqueValuesFromFeatureClassField(featureClass, 'DCA_CODE')
for DCAValue in DCAValues:
    selectTableName = 'ADS_Expanded_{}_{}'.format(DCAValue, year)
    arcpy.TableSelect_analysis(
        tableName,
        os.path.join(outputGDB, selectTableName),
        'DCA_CODE = {}'.format(DCAValue))

    arcpy.AddField_management(selectTableName, 'ORIGINAL_ID', 'LONG')
    arcpy.CalculateField_management(
        selectTableName, 'ORIGINAL_ID', '!ADS_OBJECTID!', 'PYTHON_9.3')

   # because of descrepancies in the current ADS data these two lines of code below may
   # need to be uncommented to make sure the correct acres field is created in the output

    #arcpy.AddField_management(selectTableName, 'ACRES_FINAL', 'FLOAT')
    #arcpy.CalculateField_management(selectTableName, 'ACRES_FINAL', '!shape.area@acres!', "PYTHON_9.3")

    arcpy.AddField_management(selectTableName, 'DUPLICATE', 'SHORT')

    arcpy.DeleteField_management(selectTableName, 'HOST')
    
    arcpy.DeleteField_management(selectTableName, 'MidPoint')
    arcpy.AddField_management(selectTableName, 'MidPoint', 'SHORT')
    ADSFunctions.computeADSMidPoint(
        selectTableName, 'Severity_Class', 'MidPoint')

    arcpy.AddField_management(selectTableName, 'HOST', 'SHORT')
    arcpy.CalculateField_management(
        selectTableName, 'HOST', '!HOST_CODE!', "PYTHON_9.3")

    arcpy.AddField_management(selectTableName, 'DMG_TYPE', 'SHORT')
    arcpy.CalculateField_management(
        selectTableName, 'DMG_TYPE', '!DAMAGE_TYPE_CODE!', "PYTHON_9.3")

    NRGG.deleteUneededFields(selectTableName,
    [
        'ORIGINAL_ID',
        'TPA',
        'DCA_CODE',
        'HOST',
        'DMG_TYPE',
        'Acres_Mapped',
        'DUPLICATE',
        'SeverityWeightedAcres',
        'Severity_Class',
        'MidPoint'
        ])
    arcpy.AlterField_management(selectTableName, 'Acres_Mapped', 'ACRES')
