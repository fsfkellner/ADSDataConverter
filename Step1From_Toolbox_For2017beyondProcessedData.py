########### Import statements ####################
import os
import arcpy
import sys

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions
###########################################################
outPutGDBPath = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\Merged_Historic_ADS_Data.gdb'
topLevelADSFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R1_Expanded_ADS_Tables'
# workingFolder =  os.path.dirname(parameters[0].valueAsText)

startYear = 2017
endYear = 2020

scratchGDB = arcpy.env.workspace
DCAValues = [11000, 11002, 11006, 11007, 11009, 11015, 11029, 11049, 11050, 11900, 12000, 12003, 12011, 12014, 12015, 12037, 12039, 12040, 12047, 12049, 12080, 12083, 12096, 12104, 12116, 12117, 12123, 12128, 12139, 12146, 12159, 12160, 12203, 12900, 14003, 14039, 14040, 19000, 21000, 21001, 21017, 22057, 23001, 23011, 23023, 24008, 25000, 25002, 25005, 25022, 25028, 25033, 25034, 25035, 25039, 25050, 25058, 25062, 25074, 26001, 26002, 26004, 30000, 30001, 41000, 50002, 50003, 50004, 50005, 50006, 50011, 50012, 50013, 50014, 50015, 50017, 50800, 70000, 80002, 90000, 90008, 90009, 90010]
damgeCodesList = None
region = 'R1'

DCAValues = [int(DCAValue) for DCAValue in DCAValues]
featureClasses = ADSFunctions.findAllFeatureClasses(
    topLevelADSFolder, 'Damage')

decadeFilteredFeatureClasses = ADSFunctions.getDecadeCopyFeatureClasses(
    featureClasses, startYear, endYear + 1)

for featureClass in decadeFilteredFeatureClasses:
    layerViewName = '{}_View'.format(
        os.path.basename(featureClass.replace('_Copy', '')))
    arcpy.MakeFeatureLayer_management(featureClass, layerViewName)

    adsGDB = os.path.dirname(featureClass)
    arcpy.env.workspace = adsGDB
    for DCAValue in DCAValues:
        individualDCATables = [
            os.path.join(adsGDB, table) for table in arcpy.ListTables(
                '*{}*'.format(DCAValue)) if 'Copy' not in table]

        for individualTable in individualDCATables:
            year = individualTable[-4:]
            arcpy.AddMessage('Working on ' + table)
            table = '{}_View'.format(os.path.basename(individualTable))
            arcpy.MakeTableView_management(individualTable, table)
            selectTableName = '{}_Copy'.format(
                os.path.basename(individualTable))

            selectTablePath = os.path.join(
                    scratchGDB, selectTableName)
            arcpy.TableSelect_analysis(
                    table, selectTablePath, '1=1')

            arcpy.MakeTableView_management(
                selectTablePath, selectTableName)

            #mergedTableName = '{}_{}'.format(region, table.replace(
            #    'Expanded', '').replace('_View', ''))
            mergedTableName = 'ADS_Expanded_{}_{}_Copy_Merged'.format(DCAValue, year)

            arcpy.TableToTable_conversion(selectTableName, outPutGDBPath, mergedTableName)

            arcpy.MakeTableView_management(
                os.path.join(outPutGDBPath, mergedTableName),
                mergedTableName)

            ids = ADSFunctions.returnAllValuesFromField(
                mergedTableName, 'ORIGINAL_ID')

            ids = NRGG.listStringJoiner(ids)
            featureClassName = '{}_ADS_{}_Merged_{}'.format(region, DCAValue, year)

            ADSFunctions.selectPolygonsFromOriginalData(
                layerViewName, ids,
                featureClassName, outPutGDBPath)

            arcpy.MakeFeatureLayer_management(
                os.path.join(outPutGDBPath, featureClassName),
                featureClassName)

            ADSFunctions.deleteUneededFields(
                featureClassName, ['ADS_OBJECTID'])

            arcpy.JoinField_management(
                featureClassName,
                'ADS_OBJECTID',
                mergedTableName,
                'ORIGINAL_ID',
                'ORIGINAL_ID;DUPLICATE;TPA;DCA_CODE;HOST;ACRES_FINAL;SeverityWeightedAcres;MidPoint')