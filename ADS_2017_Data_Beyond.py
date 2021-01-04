import arcpy
import os

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions

featureClass = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R1_208_ADS_Data\R1ADS2018.gdb\R1ADS2018Damage'
year= 2018

outputGDB = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R1_Expanded_ADS_Tables\R1ADS_SingleDCAValue_Tables_2018.gdb'
copyName = '{}_copy'.format(os.path.basename(featureClass))
arcpy.FeatureClassToFeatureClass_conversion(featureClass, outputGDB, copyName)

ADSFunctions.makeCopyOfOriginalOBJECTID('{}_copy'.format(os.path.basename(featureClass)))
tableName = '{}_TableView'.format(os.path.basename(featureClass))
arcpy.MakeTableView_management(os.path.join(outputGDB, copyName), tableName)

DCAValues = ADSFunctions.uniqueValuesFromFeatureClassField(featureClass, 'DCA_CODE')
for DCAValue in DCAValues:
    selectTableName = 'ADS_Expanded_{}_{}'.format(DCAValue, year)
    arcpy.TableSelect_analysis(tableName, os.path.join(outputGDB, selectTableName), 'DCA_CODE = {}'.format(DCAValue))

    arcpy.AddField_management(selectTableName, 'ORIGINAL_ID', 'LONG')
    arcpy.CalculateField_management(selectTableName, 'ORIGINAL_ID', '!ADS_OBJECTID!', 'PYTHON_9.3')
   
    #arcpy.AddField_management(selectTableName, 'ACRES_FINAL', 'FLOAT')
    #arcpy.CalculateField_management(selectTableName, 'ACRES_FINAL', '!Acres!', "PYTHON_9.3")

    arcpy.AddField_management(selectTableName, 'DUPLICATE', 'SHORT')

    arcpy.DeleteField_management(selectTableName, 'HOST')
    arcpy.AddField_management(selectTableName, 'HOST', 'SHORT')
    arcpy.CalculateField_management(selectTableName, 'HOST', '!HOST_CODE!', "PYTHON_9.3")

    arcpy.AddField_management(selectTableName, 'DMG_TYPE', 'SHORT')
    arcpy.CalculateField_management(selectTableName, 'DMG_TYPE', '!DAMAGE_TYPE_CODE!', "PYTHON_9.3")

    ADSFunctions.deleteUneededFields(selectTableName, ['ORIGINAL_ID', 'TPA', 'DCA_CODE', 'HOST', 'DMG_TYPE', 'ACRES_FINAL', 'DUPLICATE', 'SeverityWeightedAcres', 'Severity_Class', 'MidPoint'])
    arcpy.AlterField_management(selectTableName, 'ACRES_FINAL', 'ACRES')
