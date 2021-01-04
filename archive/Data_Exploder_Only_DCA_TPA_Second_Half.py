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

topLevelADSFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\DASM'
workingFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\WorkingFolder'
scratchGDB = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\WorkingFolder\Scratch.gdb'
damgeCodesList = [1, 2]
region = 'R1'

featureClasses = ADSFunctions.findAllFeatureClasses(
    topLevelADSFolder, 'Damage')
# a folder where output GDBs will be written to
for featureClass in featureClasses:
    layerViewName = '{}_View'.format(os.path.basename(featureClass.replace('_Copy', '')))
    arcpy.MakeFeatureLayer_management(featureClass, layerViewName)

    adsGDB = os.path.dirname(featureClass)
    arcpy.env.workspace = adsGDB
    outPutGDB = '{}_Merged.gdb'.format(os.path.basename(featureClass.replace('_Copy', '')))
    outPutGDBPath = ADSFunctions.makeNewGDBIfDoesntExist(workingFolder, outPutGDB)

    individualDCATables = [os.path.join(adsGDB, table) for table in arcpy.ListTables()]
    for individualTable in individualDCATables:
        print('Working on', table)
        table = '{}_View'.format(os.path.basename(individualTable))
        arcpy.MakeTableView_management(individualTable, table)
        whereStatement = ADSFunctions.makeDamageCodeWhereStatement(
            damgeCodesList)
        if ADSFunctions.checkForDamageCodes(table, whereStatement):
            selectTableName = '{}_Selected'.format(os.path.basename(table))
            selectTablePath = os.path.join(scratchGDB, selectTableName)
            arcpy.TableSelect_analysis(table, selectTablePath, whereStatement)
            duplicateIDS = ADSFunctions.returnAllValuesFromField(
                selectTableName, 'ORIGINAL_ID')
            arcpy.CalculateField_management(
                selectTableName, 'DUPLICATE', 'None',  'PYTHON_9.3')

            duplicateIDS = ADSFunctions.returnDuplicates(duplicateIDS)
            mergedTableName = '{}_{}'.format(region, table.replace('Expanded', 'Merged').replace('_View', ''))
            featureClassName = '{}_{}_Merged'.format(region, table.replace('_Expanded', '').replace('_View', ''))
            if duplicateIDS:
                arcpy.CalculateField_management(
                    selectTableName, 'DUPLICATE', 'ORIGINAL_ID IN {}'.format(set(ids)))
                mergedTableName = ADSFunctions.mergeDuplicatesNoHost(
                    selectTableName, outPutGDBPath)
            else:
                arcpy.TableToTable_conversion(selectTableName, outPutGDBPath, mergedTableName)

            ids = ADSFunctions.returnAllValuesFromField(
                mergedTableName, 'ORIGINAL_ID')
            ids = NRGG.listStringJoiner(ids)
            ADSFunctions.selectPolygonsFromOriginalData(
                layerViewName, ids,
                featureClassName, outPutGDBPath)
            ADSFunctions.deleteUneededFields(featureClassName, ['ADS_OBJECTID'])
            arcpy.JoinField_management(
                featureClassName, 'ADS_OBJECTID', mergedTableName,
                'ORIGINAL_ID', 'ORIGINAL_ID;DUPLICATE;TPA;DCA_CODE;HOST;ACRES')