import os
from collections import Counter
import arcpy 
import sys
sys.path.append(r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner')
import DataExplorerFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\NRGG_Tools')
import NRGG

tbx = arcpy.ImportToolbox(r'T:\FS\Reference\GeoTool\r01\Toolbox\NRGGFieldCalculator\NRGGFieldCalculator.pyt')
fc = r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner\ADS_Testing\R1ADS1999.gdb\R1ADS1999Damage'
outPutGDB = r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner\ADS_Testing\Data_Exploder.gdb'

layerViewName = os.path.basename(fc)
year = DataExplorerFunctions.findDigit(layerViewName)[1:]
year = NRGG.listStringJoiner(year, '')

tableName = 'ADS_Expanded'
tableInMemoryPath = os.path.join('in_memory', tableName)

arcpy.MakeFeatureLayer_management(fc, layerViewName)
arcpy.TableSelect_analysis(layerViewName, tableInMemoryPath)
arcpy.AddField_management(tableInMemoryPath, 'ORIGINAL_ID', 'LONG')
arcpy.AddField_management(tableInMemoryPath, 'DUPLICATE', 'SHORT')
arcpy.AddField_management(tableInMemoryPath, 'TPA', 'FLOAT')
arcpy.AddField_management(tableInMemoryPath, 'DCA', 'LONG')
arcpy.DeleteRows_management(tableName)
arcpy.DeleteField_management(tableName, '''AREA;PERIMETER;ADS99_APP_;
    ADS99_APP_ID;DATA;MAP;BUG1;BUG2;BUG3;ORGAC;NO_TREES1;NO_TREES2;
    NO_TREES3;TPA1;TPA2;TPA3;HOST1;HOST2;HOST3;SEVERITY1;SEVERITY2;
    SEVERITY3;FOR_TYPE1;FOR_TYPE2;FOR_TYPE3;DMG_TYPE1;DMG_TYPE2;DMG_TYPE3;
    PATTERN1;PATTERN2;PATTERN3;DCA1;DCA2;DCA3;SURVEY_ID1;SURVEY_ID2;
    SURVEY_ID3;NOTES;Shape_Length;Shape_Area''')


cursor = arcpy.da.SearchCursor(layerViewName, ['DCA1', 'DCA2', 'DCA3'])
uniqueDCAValues = list(
    set(row for rows in cursor for row in rows if row != 99999))
uniqueDCAValues.sort()
print(uniqueDCAValues)

easyDict = DataExplorerFunctions.easyValues(layerViewName, uniqueDCAValues)

cursor = arcpy.da.InsertCursor(tableName,
    ['ORIGINAL_ID', 'TPA', 'DCA_CODE', 'ACRES'])
for key in easyDict:
    rowList = list(easyDict[key])
    rowList.insert(0, key)
    cursor.insertRow(rowList)
print(arcpy.GetCount_management(tableName)[0])
del(key)

diffCausDict = DataExplorerFunctions.difficultValues(layerViewName, easyDict)

print(len(diffCausDict))

cursor = arcpy.da.InsertCursor(tableName,
    ['ORIGINAL_ID', 'TPA', 'DCA', 'ACRES', 'DUPLICATE'])
for key in diffCausDict:
    if diffCausDict[key]:
        if len(diffCausDict[key]) <= 1:
            for causList in diffCausDict[key]:
                causList.insert(0,key)
                causList.append(None)
                cursor.insertRow(causList)
        else:
            count = 0
            for causList in diffCausDict[key]:
                if count >= 1:
                    causList.insert(0,str(key))
                    causList.append(1)
                    cursor.insertRow(causList)
                    count += 1
                else:
                    causList.insert(0,str(key))
                    causList.append(None)
                    cursor.insertRow(causList)
                    count += 1
print(arcpy.GetCount_management(tableName)[0])
del(key)

finalTableName = 'ADS_Expanded_{0}'.format(year)
arcpy.TableToTable_conversion(
    tableName, outPutGDB, finalTableName)

ids = dict(Counter(
    [row[0] for row in arcpy.da.SearchCursor(
        os.path.basename(tableName), 'ORIGINAL_ID')]))
dict((k, v) for k, v in ids.items() if v == 2)

NEW_IDS = [row[0] for row in arcpy.da.SearchCursor(
    os.path.basename(tableName), 'ORIGINAL_ID')]
cursor = arcpy.da.SearchCursor(layerViewName, 'OBJECTID')
for row in cursor:
    if row[0] not in NEW_IDS:
        print row[0]

#arcpy.AddJoin_management(
#    layerViewName, 'OBJECTID', finalTableName, 'ORIGINAL_ID', 'KEEP_ALL')

DCAFiles = []
for DCA in uniqueDCAValues:
    print('Working on DCA value {}'.format(DCA))
    # make table of only single DCA values
    tableQuery = 'DCA = {}'.format(DCA)
    cursor = arcpy.da.SearchCursor(finalTableName, "ORIGINAL_ID", tableQuery)
    ids = [row[0] for row in cursor]
    ids = str(tuple(ids))
    DCATable = 'ADS_1999_Table_{}'.format(DCA)
    arcpy.TableToTable_conversion(finalTableName, arcpy.env.workspace, DCATable, tableQuery)

    DCAFeature = 'ADS_1999_{}'
    featureClassQuery = 'OBJECTID IN {}'.format(ids)
    featureClassDCAName = 'ADS_1999_{}'.format(DCA)
    arcpy.FeatureClassToFeatureClass_conversion(
        layerViewName, arcpy.env.workspace,
        featureClassDCAName, featureClassQuery, 
        'ADS_OBJECTID "ADS_OBJECTID" true true false 4 Long 0 0 ,First,#,R1ADS1999Damage,ADS_OBJECTID,-1,-1', '#')

    arcpy.JoinField_management(
        featureClassDCAName,
        'ADS_OBJECTID',
        DCATable,
        'ORIGINAL_ID', 'DUPLICATE;TPA;DCA')

    DCAFiles.append(featureClassDCAName)

    """ query = 'R1ADS1999Damage.OBJECTID = ADS_Expanded_1999.ORIGINAL_ID AND {}.DCA = {}'.format(finalTableName, DCA)
    cursor = arcpy.da.SearchCursor(finalTableName, "ORIGINAL_ID", 'DCA = {}'.format(DCA))
    ids = [row[0] for row in cursor]
    ids = str(tuple(ids))
    query = 'OBJECTID IN {}.format(ids)
    arcpy.SelectLayerByAttribute_management(
        layerViewName, 'NEW_SELECTION', query)

    featureName = 'ADS_{}_{}'.format(year, DCA)

    dropFields = '''ADS_Expanded_1999_OBJECTID "ADS_Expanded_1999_OBJECTID" false true false 4 Long 0 9 ,
    First,#,R1ADS1999Damage,ADS_Expanded_1999.OBJECTID,-1,-1;
    ADS_Expanded_1999_ACRES "ADS_Expanded_1999_ACRES" true true false 4 Float 0 0 ,
    First,#,R1ADS1999Damage,ADS_Expanded_1999.ACRES,-1,-1;
    ADS_Expanded_1999_ORIGINAL_ID "ADS_Expanded_1999_ORIGINAL_ID" true true false 4 Long 0 0 ,
    First,#,R1ADS1999Damage,ADS_Expanded_1999.ORIGINAL_ID,-1,
    -1;ADS_Expanded_1999_DUPLICATE "ADS_Expanded_1999_DUPLICATE" true true false 2 Short 0 0 ,
    First,#,R1ADS1999Damage,ADS_Expanded_1999.DUPLICATE,-1,
    -1;ADS_Expanded_1999_TPA "ADS_Expanded_1999_TPA" true true false 4 Float 0 0 ,
    First,#,R1ADS1999Damage,ADS_Expanded_1999.TPA,-1,-1;
    ADS_Expanded_1999_DCA "ADS_Expanded_1999_DCA" true true false 4 Long 0 0 ,
    First,#,R1ADS1999Damage,ADS_Expanded_1999.DCA,-1,-1'''

    arcpy.FeatureClassToFeatureClass_conversion(
        'R1ADS1999Damage',
        arcpy.env.workspace,
        featureName, '#', dropFields, '#')

    fields = [
        ['ACRES', 'DOUBLE'],
        ['DCA', 'LONG'],
        ['TPA', 'FLOAT']]
    
"""     """ duplicateCheck = [field.name for field in arcpy.ListFields(featureName) if 'DUP' in field.name]
    if  duplicateCheck:
        fields.append(['DUPLLICATE', 'SHORT']) """ """

    for addField in fields:
        arcpy.AddField_management(featureName, addField[0], addField[1])
        fieldWithValues = '{}_{}'.format(finalTableName, addField[0])
        tbx.CalculateFields(
            featureName, 'OBJECTID', addField[0], fieldWithValues)
    dropFields = [field.name for field in arcpy.ListFields(featureName) if 'ADS' in field.name and not field.required]
    arcpy.DeleteField_management(featureName, dropFields)
    DCAFiles.append(featureName)

    arcpy.SelectLayerByAttribute_management(layerViewName, 'CLEAR_SELECTION') """

# mergeName = os.path.join(outPutGDB, 'R1R4Final_ADS_{}_Expanded'.format(year))
# arcpy.Merge_management(DCAFiles,os.path.join(outPutGDB, mergeName))
# arcpy.AlterField_management(mergeName, "DCA","DCA_CODE", "DCA_CODE")
# arcpy.AlterField_management(mergeName, "ACRES","FINAL_ACRES", "FINAL_ACRES")





# def returnDuplicates(yourList):
#     notDuplicate = set()
#     isDuplicate = set()
#     notDuplicate_add = notDuplicate.add
#     isDuplicate_add = isDuplicate.add
#     for item in yourList:
#         if item in notDuplicate:
#             isDuplicate(item)
#         else:
#             notDuplicate_add(item)
#     return list(isDuplicate)
# cursor = arcpy.da.SearchCursor("ADS_Data_1999_11015", 'ADS_Exploded_11015_ORIGINAL_ID')
# allValuesList = [row[0] for row in cursor ]