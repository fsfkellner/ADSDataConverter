import arcpy
import os


def deleteUneededFields(featureClass, fieldsToKeep):
    fieldsToDelete = [
        field.name for field in arcpy.ListFields(featureClass)
        if field.name not in fieldsToKeep
        and not field.required]
    arcpy.DeleteField_management(featureClass, fieldsToDelete)


def makeEmptyADSTable(nameOfTable, outputWorkspace):
    tableName = nameOfTable
    arcpy.CreateTable_management(outputWorkspace, tableName)
    arcpy.AddField_management(tableName, 'ORIGINAL_ID', 'LONG')
    arcpy.AddField_management(tableName, 'DUPLICATE', 'SHORT')
    arcpy.AddField_management(tableName, 'TPA', 'FLOAT')
    arcpy.AddField_management(tableName, 'DCA_CODE', 'LONG')
    arcpy.AddField_management(tableName, 'HOST', 'SHORT')
    arcpy.AddField_management(tableName, 'ACRES', 'FLOAT')


def makeCopyOfOriginalOBJECTID(featurClass):
    arcpy.AddField_management(featurClass, "ADS_OBJECTID", 'LONG')
    arcpy.CalculateField_management(
        featurClass, 'ADS_OBJECTID', '!OBJECTID!', 'PYTHON', '#')


def getADSDCACodes(excelFile):
    codes = pd.read_excel(excelFile)
    codes = codes['Code'].tolist()
    return codes


def findDigit(stringText):
    textList = []
    for character in stringText:
        if character.isdigit():
            textList.append(character)
    return textList


def setDamageToZero(featureClass):
    numbers = [1, 2, 3]
    for number in numbers:
        cursor = arcpy.da.UpdateCursor(
                featureClass,
                [
                    'DMG_TYPE{}'.format(number),
                    'DCA{}'.format(number),
                    'TPA{}'.format(number)
                ],
                'DMG_TYPE{} NOT IN (1, 2)'.format(number))
        for row in cursor:
            row[0] = -1
            row[1] = 99999
            row[2] = -1
            cursor.updateRow(row)


def uniqueValuesFromFeatureField(featureClass, field):
    with arcpy.da.SearchCursor as cursor:
        uniqueValues = list(set(row[0] for row in cursor))
    return uniqueValues


def convertNonDCAValuesToNull(inputTable, DCAValue):
    for number in range(1, 4):
            fields = [
                'DCA{}'.format(number),
                'TPA{}'.format(number),
                'HOST{}'.format(number)]
            cursor = arcpy.da.UpdateCursor(inputTable, fields)
            for row in cursor:
                if row[0] != DCAValue and row[0] != 99999:
                    row[0] = 99999
                    row[1] = -1
                    row[2] = -1
                cursor.updateRow(row)


def getEveryRecordForSingleDCAValue(featureClass, DCAValue, scratchWorkspace):
    DCADict = {}
    scratchWorkspace = scratchWorkspace
    outputTableName = 'DCA{}'.format(DCAValue)
    outputTableNamePath = os.path.join('in_memory', outputTableName)

    arcpy.TableSelect_analysis(
        featureClass,
        outputTableNamePath,
        'DCA1 = {0} OR DCA2 = {0} OR DCA3 = {0}'.format(DCAValue))

    convertNonDCAValuesToNull(outputTableName, DCAValue)

    for number in range(1, 4):
        fields = [
            'ADS_OBJECTID',
            'TPA{}'.format(number),
            'DCA{}'.format(number),
            'HOST{}'.format(number),
            'ACRES']
        cursor = arcpy.da.SearchCursor(outputTableName, fields)
        for row in cursor:
            if row[0] not in DCADict.keys() and row[2] == DCAValue:
                DCADict[row[0]] = []
                DCADict[row[0]].append([row[1], row[2], row[3], row[4]])
            elif row[0] in DCADict.keys() and row[2] == DCAValue:
                DCADict[row[0]].append([row[1], row[2], row[3], row[4]])

    return DCADict


def findAllFeatureClasses(folder):
    featureClasses = []
    walk = arcpy.da.Walk(folder, datatype="FeatureClass")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if 'Damage' in os.path.join(dirpath, filename):
                featureClasses.append(os.path.join(dirpath, filename))
    return featureClasses


def getAllUniqueDCAValues(featureClass):
    cursor = arcpy.da.SearchCursor(featureClass, ['DCA1', 'DCA2', 'DCA3'])
    uniqueDCAValues = list(
        set(row for rows in cursor for row in rows if row != 99999))
    uniqueDCAValues.sort()
    return uniqueDCAValues


def updateTablewithEveryDCARecord(tableName, everyDCARecordDict):
    cursor = arcpy.da.InsertCursor(
            tableName,
            ['ORIGINAL_ID', 'TPA', 'DCA_CODE', 'HOST', 'ACRES', 'DUPLICATE'])

    for key in everyDCARecordDict:
        if everyDCARecordDict[key]:
            if len(everyDCARecordDict[key]) <= 1:
                for causList in everyDCARecordDict[key]:
                    causList.insert(0, key)
                    causList.append(None)
                    cursor.insertRow(causList)
            else:
                count = 0
                for causList in everyDCARecordDict[key]:
                    if count >= 1:
                        causList.insert(0, str(key))
                        causList.append(1)
                        cursor.insertRow(causList)
                        count += 1
                    else:
                        causList.insert(0, str(key))
                        causList.append(None)
                        cursor.insertRow(causList)
                        count += 1


def mergeDuplicatesNoHost(tableName, workspace):
    cursor = arcpy.da.SearchCursor(
        tableName, ['ORIGINAL_ID', 'TPA'], 'DUPLICATE = 1')
    duplicatDict = {row[0]: row[1] for row in cursor}

    mergedTableName = '{}_Merged'.format(tableName)
    arcpy.TableToTable_conversion(tableName, workspace, mergedTableName)

    cursor = arcpy.da.UpdateCursor(
        mergedTableName, ['ORIGINAL_ID', 'TPA'], 'DUPLICATE IS NULL')
    for row in cursor:
        if row[0] in duplicatDict.keys():
            row[1] = row[1] + duplicatDict[row[0]]
        cursor.updateRow(row)

    arcpy.SelectLayerByAttribute_management(
        mergedTableName, "NEW_SELECTION", 'DUPLICATE = 1')
    arcpy.DeleteRows_management(mergedTableName)
    arcpy.SelectLayerByAttribute_management(mergedTableName, "CLEAR_SELECTION")


def returnDuplicates(yourList):
    notDuplicate = set()
    isDuplicate = set()
    notDuplicate_add = notDuplicate.add
    isDuplicate_add = isDuplicate.add
    for item in yourList:
        if item in notDuplicate:
            isDuplicate_add(item)
        else:
            notDuplicate_add(item)
    return list(isDuplicate)
