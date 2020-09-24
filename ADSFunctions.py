import arcpy
import os


def findDigits(stringText):
    '''Takes a string of text and returns
    all the digits found in the string
    and returns a list of those digits
    '''
    textList = []
    for character in stringText:
        if character.isdigit():
            textList.append(character)
    return textList


def deleteUneededFields(featureClass, fieldsToKeep):
    '''Provide a list of fields to keep within the featureclass
    and all other fields that are not required will be deleted
    '''
    fieldsToDelete = [
        field.name for field in arcpy.ListFields(featureClass)
        if field.name not in fieldsToKeep
        and not field.required]
    arcpy.DeleteField_management(featureClass, fieldsToDelete)


def makeEmptyADSTable(nameOfTable, outputWorkspace):
    '''Makes an empty table with the apporiate fields
    so historic ADS data can populated representing a 
    single record for each value found in DCA1, DCA2 and DCA3
    '''
    tableName = nameOfTable
    arcpy.CreateTable_management(outputWorkspace, tableName)
    arcpy.AddField_management(tableName, 'ORIGINAL_ID', 'LONG')
    arcpy.AddField_management(tableName, 'DUPLICATE', 'SHORT')
    arcpy.AddField_management(tableName, 'TPA', 'FLOAT')
    arcpy.AddField_management(tableName, 'DCA_CODE', 'LONG')
    arcpy.AddField_management(tableName, 'HOST', 'SHORT')
    arcpy.AddField_management(tableName, 'ACRES', 'FLOAT')


def makeNewGDBIfDoesntExist(folder, GDBName):
    '''Makes a new file geodatabase if the
    GDB does not already exist. Returns the the path
    of the GDB
    '''
    if arcpy.Exists(os.path.join(folder, GDBName)):
        pass
    else:
        arcpy.CreateFileGDB_management(folder, GDBName)

    GDBPath = os.path.join(folder, GDBName)
    return GDBPath


def makeCopyOfOriginalOBJECTID(featurClass):
    '''Adds a new fields "ADS_OBJECTID" so that
    single DCA values can be traced back to the original data
    '''
    arcpy.AddField_management(featurClass, "ADS_OBJECTID", 'LONG')
    arcpy.CalculateField_management(
        featurClass, 'ADS_OBJECTID', '!OBJECTID!', 'PYTHON', '#')


def setDamageToZero(featureClass):
    '''Sets the Damage Type 1, 2 or 3
    fields to null if that values don't equal
    1 or 2 which represent mortality or defoliation
    should only be used in a copy of the ADS data
    '''
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


def uniqueValuesFromFeatureClassField(featureClass, field):
    '''Returns the unique values from a
    fields in a feature class
    '''
    with arcpy.da.SearchCursor as cursor:
        uniqueValues = list(set(row[0] for row in cursor))
    return uniqueValues


def convertNonDCAValuesToNull(inputTable, DCAValue):
    '''Converts and values in DCA1, DCA2 or DCA3 that are not
    equal to the input DCAValue. The TPA and HOST fields
    associated with DCA1, DCA2 or DCA3 are
    set to null values as well.
    '''
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
    '''Returns a dictionary with key values representing the historic ADS
    data's Original OBJECTID and values of
    TPA, DCA, HOST and ACRES for each unique DCAValue
    '''
    DCADict = {}
    outputTableName = 'DCA{}'.format(DCAValue)
    outputTableNamePath = os.path.join(scratchWorkspace, outputTableName)

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
    '''Returns a list of all the feature classes
    that are within and the provided folder and any
    addtionaly subfolders
    '''
    featureClasses = []
    walk = arcpy.da.Walk(folder, datatype="FeatureClass")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if 'Damage' in os.path.join(dirpath, filename):
                featureClasses.append(os.path.join(dirpath, filename))
    return featureClasses


def getAllUniqueDCAValues(featureClass):
    '''Returns a list of all the unique DCA values
    from the 3 fields in the Historic ADS data
    DCA1, DCA2, DCA3
    '''
    cursor = arcpy.da.SearchCursor(featureClass, ['DCA1', 'DCA2', 'DCA3'])
    uniqueDCAValues = list(
        set(row for rows in cursor for row in rows if row != 99999))
    uniqueDCAValues.sort()
    return uniqueDCAValues


def returnAllValuesFromField(featureClass, field):
    allValues = [row[0] for row in arcpy.da.SearchCursor(featureClass, field)]
    allValues.sort()
    return allValues


def selectPolygonsFromOriginalData(
        featureClass, stringListOfIDs, outputName, workspace):
    outPutPath = os.path.join(workspace, outputName)
    arcpy.Select_analysis(
        featureClass,
        outPutPath, 'ADS_OBJECTID IN ({})'.format(stringListOfIDs))


def returnDuplicates(yourList):
    '''Takes an input list and returns
    a list of only the duplicate values
    '''
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


def updateTablewithEveryDCARecord(tableName, everyDCARecordDict):
    '''Takes an empty table with appropriate fields added
    to it and updates so each unique DCA value
    gets a row in the input table
    '''
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
    '''Takes the table of Expanded DCA values,
    where every row represents a unique record
    and combines the TPA for duplicates resulting from
    the same DCA value but different HOST values
    '''
    mergedTableName = '{}_Merged'.format(tableName)
    cursor = arcpy.da.SearchCursor(
        tableName, ['ORIGINAL_ID', 'TPA'], 'DUPLICATE = 1')
    duplicatDict = {row[0]: row[1] for row in cursor}

    if duplicatDict:
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
        arcpy.SelectLayerByAttribute_management(
            mergedTableName, "CLEAR_SELECTION")
    else:
        arcpy.TableToTable_conversion(tableName, workspace, mergedTableName)
    return mergedTableName

# def getADSDCACodes(excelFile):
#     codes = pd.read_excel(excelFile)
#     codes = codes['Code'].tolist()
#     return codes
