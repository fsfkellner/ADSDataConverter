import arcpy
import os

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions

featureClass = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R4_ADS_Data\2017\R4ADS2017.gdb\R4ADS2017Damage'
year= 2017

outputGDB = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R4_Expanded_ADS_Tables\R4ADS_SingleDCAValue_Tables_2017.gdb'
copyName = '{}_copy'.format(os.path.basename(featureClass))
arcpy.FeatureClassToFeatureClass_conversion(featureClass, outputGDB, copyName)

ADSFunctions.makeCopyOfOriginalOBJECTID('{}_copy'.format(os.path.basename(featureClass)))
tableName = '{}_TableView'.format(os.path.basename(featureClass))
arcpy.MakeTableView_management(os.path.join(outputGDB, copyName), tableName)

DCAValues = NRGG.uniqueValuesFromFeatureClassField(featureClass, 'DCA_CODE')
for DCAValue in DCAValues:
    selectTableName = 'ADS_Expanded_{}_{}'.format(DCAValue, year)
    arcpy.TableSelect_analysis(tableName, os.path.join(outputGDB, selectTableName), 'DCA_CODE = {}'.format(DCAValue))

    arcpy.AddField_management(selectTableName, 'ORIGINAL_ID', 'LONG')
    arcpy.CalculateField_management(selectTableName, 'ORIGINAL_ID', '!ADS_OBJECTID!', 'PYTHON_9.3')
   
    arcpy.AddField_management(selectTableName, 'ACRES_FINAL', 'FLOAT')
    arcpy.CalculateField_management(selectTableName, 'ACRES_FINAL', '!ACRES!', "PYTHON_9.3")

    arcpy.AddField_management(selectTableName, 'DUPLICATE', 'SHORT')

    arcpy.DeleteField_management(selectTableName, 'HOST')
    
    arcpy.DeleteField_management(selectTableName, 'MidPoint')
    arcpy.AddField_management(selectTableName, 'MidPoint', 'SHORT')
    ADSFunctions.computeADSMidPoint(selectTableName, 'Severity_Class', 'MidPoint')

    arcpy.AddField_management(selectTableName, 'HOST', 'SHORT')
    arcpy.CalculateField_management(selectTableName, 'HOST', '!HOST_CODE!', "PYTHON_9.3")

    arcpy.AddField_management(selectTableName, 'DMG_TYPE', 'SHORT')
    arcpy.CalculateField_management(selectTableName, 'DMG_TYPE', '!DAMAGE_TYPE_CODE!', "PYTHON_9.3")

    NRGG.deleteUneededFields(selectTableName, ['ORIGINAL_ID', 'TPA', 'DCA_CODE', 'HOST', 'DMG_TYPE', 'ACRES_FINAL', 'DUPLICATE', 'SeverityWeightedAcres', 'Severity_Class', 'MidPoint'])
    arcpy.AlterField_management(selectTableName, 'ACRES_FINAL', 'ACRES')
