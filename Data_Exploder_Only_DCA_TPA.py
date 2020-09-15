import os
from collections import Counter
import arcpy 
import sys
sys.path.append(r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner')
import DataExplorerFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\NRGG_Tools')
import NRGG

tbx = arcpy.ImportToolbox(r'T:\FS\Reference\GeoTool\r01\Toolbox\NRGGFieldCalculator\NRGGFieldCalculator.pyt')
fc = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R01\ADS\Archived\Yearly\WithFNF\1999\R1ADS1999.gdb\R1ADS1999Damage'
outPutGDB = r'T:\FS\NFS\R01\Program\7140Geometronics\GIS\Workspace\fkellner\ADS_Testing\Data_Exploder.gdb'

scratchWorkspace = arcpy.env.workspace

# featureClassesToDelete = arcpy.ListFeatureClasses('*ADS')
# for featureClass in featureClassesToDelete:
#     arcpy.Delete_management(featureClass)
# arcpy.Compact_management(scratchWorkspace)

# tablessToDelete = arcpy.ListTables('*ADS')
# for table in tablessToDelete:
#     arcpy.Delete_management(table)

# arcpy.Compact_management(scratchWorkspace)

layerViewName = '{}_Copy'.format(os.path.basename(fc))
arcpy.FeatureClassToFeatureClass_conversion(
    fc, scratchWorkspace, layerViewName)

arcpy.AddField_management(layerViewName, "ADS_OBJECTID", 'LONG')
arcpy.CalculateField_management(layerViewName, 'ADS_OBJECTID', '!OBJECTID!', 'PYTHON', '#')
year = DataExplorerFunctions.findDigit(layerViewName)[1:]
year = NRGG.listStringJoiner(year, '')

tableName = 'ADS_Expanded'
tableInMemoryPath = os.path.join('in_memory', tableName)

arcpy.TableSelect_analysis(layerViewName, tableInMemoryPath)
arcpy.AddField_management(tableInMemoryPath, 'ORIGINAL_ID', 'LONG')
arcpy.AddField_management(tableInMemoryPath, 'DUPLICATE', 'SHORT')
arcpy.AddField_management(tableInMemoryPath, 'TPA', 'FLOAT')
arcpy.AddField_management(tableInMemoryPath, 'DCA_CODE', 'LONG')
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
    ['ORIGINAL_ID', 'TPA', 'DCA_CODE', 'ACRES', 'DUPLICATE'])
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

DCAFiles = []
for DCA in uniqueDCAValues[:2]:
    print('Working on DCA value {}'.format(DCA))
    # make table of only single DCA values
    tableQuery = 'DCA_CODE = {}'.format(DCA)
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
        'ADS_OBJECTID "ADS_OBJECTID" true true false 4 Long 0 0 ,First,#,{}},ADS_OBJECTID,-1,-1'.format(layerViewName))

    arcpy.JoinField_management(
        featureClassDCAName,
        'ADS_OBJECTID',
        DCATable,
        'ORIGINAL_ID', 'DUPLICATE;TPA;DCA_CODE;ACRES')

    DCAFiles.append(featureClassDCAName)

mergeName = os.path.join(outPutGDB, 'R1R4Final_ADS_{}_Expanded'.format(year))
arcpy.Merge_management(DCAFiles, os.path.join(outPutGDB, mergeName))
