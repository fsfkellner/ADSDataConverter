import arcpy
import os
from collections import Counter
from copy import deepcopy
import sys
sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')

from NRGG import listStringJoiner


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


def makeEmptyADSTable(tableName, outputWorkspace):
    '''Makes an empty table with the apporiate fields
    so historic ADS data can populated representing a 
    single record for each value found in DCA1, DCA2 and DCA3
    '''
    arcpy.CreateTable_management(outputWorkspace, tableName)
    arcpy.AddField_management(tableName, 'ORIGINAL_ID', 'LONG')
    arcpy.AddField_management(tableName, 'DUPLICATE', 'SHORT')
    arcpy.AddField_management(tableName, 'TPA', 'FLOAT')
    arcpy.AddField_management(tableName, 'DCA_CODE', 'LONG')
    arcpy.AddField_management(tableName, 'HOST', 'SHORT')
    arcpy.AddField_management(tableName, 'DMG_TYPE', 'SHORT')
    arcpy.AddField_management(tableName, 'ACRES', 'FLOAT')


def makeNewGDBIfDoesntExist(folder, GDBName):
    '''Makes a new file geodatabase if the
    GDB does not already exist. Returns the the path
    of the GDB
    '''
    if arcpy.Exists(os.path.join(folder, GDBName)):
        GDBPath = os.path.join(folder, GDBName)
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


def makeDamageCodeWhereStatement(damageCodesList):
    '''A function to write the where statement for select expanded ADS
    from the expanded single DCA table based off of damage code type
    '''
    if len(damageCodesList) == 1:
        whereStatement = 'DMG_TYPE = {}'.format(damageCodesList[0])
    else:
        whereStatement = 'DMG_TYPE IN {}'.format(tuple(damageCodesList))
    return whereStatement


def checkForDamageCodes(featureClass, whereStatement):
    '''This function takes a SQL where clause based off the ADS
    damage type field and checks to makes sure that those value exist in
    and expande singlge DCA table.
    '''
    arcpy.SelectLayerByAttribute_management(featureClass, "CLEAR_SELECTION")
    arcpy.SelectLayerByAttribute_management(featureClass, "NEW_SELECTION", whereStatement)
    count = int(arcpy.GetCount_management(featureClass)[0])
    arcpy.SelectLayerByAttribute_management(featureClass, "CLEAR_SELECTION")
    if count > 0:
        return True
    else:
        return False


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
    with arcpy.da.SearchCursor(featureClass, field) as cursor:
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
            'HOST{}'.format(number),
            'DMG_TYPE{}'.format(number)
            ]
        cursor = arcpy.da.UpdateCursor(inputTable, fields)
        for row in cursor:
            if row[0] != DCAValue and row[0] != 99999:
                row[0] = 99999
                row[1] = -1
                row[2] = -1
                row[3] = -1
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
            'DMG_TYPE{}'.format(number),
            'ACRES']
        cursor = arcpy.da.SearchCursor(outputTableName, fields)
        for row in cursor:
            if row[0] not in DCADict.keys() and row[2] == DCAValue:
                DCADict[row[0]] = []
                DCADict[row[0]].append([row[1], row[2], row[3], row[4], row[5]])
            elif row[0] in DCADict.keys() and row[2] == DCAValue:
                DCADict[row[0]].append([row[1], row[2], row[3], row[4], row[5]])

    return DCADict


def findAllFeatureClasses(folder, searchWord):
    '''Returns a list of all the feature classes
    that are within and the provided folder and any
    addtionaly subfolders
    '''
    featureClasses = []
    walk = arcpy.da.Walk(folder, datatype="FeatureClass")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if searchWord in os.path.join(dirpath, filename):
                featureClasses.append(os.path.join(dirpath, filename))
    return featureClasses


def findAllTables(folder, searchWord):
    '''Returns a list of all the feature classes
    that are within and the provided folder and any
    addtionaly subfolders
    '''
    tables = []
    walk = arcpy.da.Walk(folder, datatype="Table")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if searchWord in os.path.join(dirpath, filename):
                tables.append(os.path.join(dirpath, filename))
    return tables


def getAllUniqueDCAValues(featureClass):
    '''Returns a list of all the unique DCA values
    from the 3 fields in the Historic ADS data
    DCA1, DCA2, DCA3
    '''
    cursor = arcpy.da.SearchCursor(featureClass, ['DCA1', 'DCA2', 'DCA3'])
    uniqueDCAValues = list(
        set(row for rows in cursor for row in rows))
    if 99999 in uniqueDCAValues:
        uniqueDCAValues.remove(99999)
    if -1 in uniqueDCAValues:
        uniqueDCAValues.remove(-1)
    uniqueDCAValues.sort()
    return uniqueDCAValues


def returnAllValuesFromField(featureClass, field):
    '''Taks an input field and returns a sorted list off 
    all the values in a field from an table or feature class attribute table
    '''
    allValues = [row[0] for row in arcpy.da.SearchCursor(featureClass, field)]
    allValues.sort()
    return allValues


def selectPolygonsFromOriginalData(
        featureClass, stringListOfIDs, outputName, workspace):
    '''Using values from the Unique_ID field performs
    an ESRI select analysis. Where the values are selected
    and those data are exported as a new file.
    '''
    outPutPath = os.path.join(workspace, outputName)
    arcpy.Select_analysis(
        featureClass,
        outPutPath,
        'ADS_OBJECTID IN ({})'.format(stringListOfIDs))


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
            ['ORIGINAL_ID', 'TPA', 'DCA_CODE', 'HOST', 'DMG_TYPE', 'ACRES', 'DUPLICATE'])

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
    countOfIDs = Counter(returnAllValuesFromField(tableName, 'ORIGINAL_ID'))
    if 2 in countOfIDs.values() or 3 in countOfIDs.values():
        duplicatDict = {}
        cursor = arcpy.da.SearchCursor(
            tableName, ['ORIGINAL_ID', 'TPA'], 'DUPLICATE = 1')
        for row in cursor:
            if row[0] not in duplicatDict:
                duplicatDict[row[0]] = row[1]
            elif row[0] in duplicatDict:
                duplicatDict[row[0]] = row[1] + duplicatDict[row[0]]

    cursor = arcpy.da.SearchCursor(
        tableName, ['ORIGINAL_ID', 'TPA'], 'DUPLICATE = 1')
    duplicatDict = {row[0]: row[1] for row in cursor}

    if duplicatDict:
        arcpy.TableToTable_conversion(tableName, workspace, mergedTableName)
        arcpy.MakeTableView_management(
            os.path.join(workspace, mergedTableName), mergedTableName)

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


def computeSeverityWeightedAcres(
        featureClass, SeverityMidPointField, AcresField, SWAField):
    '''Compute severity weighted arces in a ADS feature class or table.'''
    fields = [SeverityMidPointField, AcresField, SWAField]
    cursor = arcpy.da.UpdateCursor(featureClass, fields)
    for row in cursor:
        row[2] = float((float(row[0])/65.0) * float(row[1]))
        cursor.updateRow(row)


def getDecadeFeatureClasses(listOfFeatureClasses, startYear, endYear):
    '''Takes a list of feature classes and returns only those that fall within
    the start and end year.
    '''
    decadeFilteredFeatureClasses = [
        featureClass for featureClass in listOfFeatureClasses
        if int(featureClass[-4:]) in range(startYear, endYear)]

    decadeFilteredFeatureClasses.sort()  
    return decadeFilteredFeatureClasses


def getDecadeCopyFeatureClasses(listOfFeatureClasses, startYear, endYear):
    '''Takes a list of feature classes and returns only those that fall within
    the start and end year.
    '''
    decadeFilteredFeatureClasses = []
    for featureClass in listOfFeatureClasses:
        featureClassBasename = os.path.basename(featureClass)
        year = findDigits(featureClassBasename)[1:]
        year = int(listStringJoiner(year, ''))

        if year in range(startYear, endYear):
            decadeFilteredFeatureClasses.append(featureClass)

    decadeFilteredFeatureClasses.sort()  
    return decadeFilteredFeatureClasses


def getDCAValuesFromFiles(listofFeatureClasses):
    '''Takes a list feature classes and returns DCA values
    that are found in the naming convention of the file.
    '''
    allDCAValues = set()
    for featureClass in listofFeatureClasses:
        DCAValue = [character for character
                    in os.path.basename(featureClass[:-5])
                    if character.isdigit()]

        DCAValue = listStringJoiner(DCAValue, '')
        allDCAValues.add(int(DCAValue))

    allDCAValues = list(allDCAValues)
    allDCAValues.sort()
    return allDCAValues


def featuresInDecadeSingleDCAValue(listofFeatureClasses, inputDCAValue):
    DCAFilteredFeatureClasses = []
    for featureClass in listofFeatureClasses:
        DCAValue = [character for character
                    in os.path.basename(featureClass)[2:-5]
                    if character.isdigit()]

        DCAValue = listStringJoiner(DCAValue, '')
        DCAValue = int(DCAValue)
        if DCAValue == inputDCAValue:
            DCAFilteredFeatureClasses.append(featureClass)

    DCAFilteredFeatureClasses.sort()
    return DCAFilteredFeatureClasses


def getYearFields(featureClass):
    yearFields = [
        field.name for field in arcpy.ListFields(featureClass)
        if 'YEAR' in field.name]
    return yearFields


def getSpecificFields(featureClass, textValue):
    TPAFields = [
        field.name for field in arcpy.ListFields(featureClass)
        if textValue in field.name]
    return TPAFields


def computeTotalYears(featureClass, yearFields):
    cursor = arcpy.da.UpdateCursor(featureClass, yearFields)
    for row in cursor:
        yearValues = deepcopy(row[:-1])
        while None in yearValues:
            yearValues.remove(None)
        row[-1] = sum(yearValues)
        cursor.updateRow(row)


def computeTotalTPA(featureClass, TPAFields):
    cursor = arcpy.da.UpdateCursor(featureClass, TPAFields)
    for row in cursor:
        TPAValues = deepcopy(row[:-1])
        while None in TPAValues:
            TPAValues.remove(None)
        row[-1] = sum(TPAValues)
        cursor.updateRow(row)


def computeUnionMidpoint(featureClass, MidPointFields):
    cursor = arcpy.da.UpdateCursor(featureClass, MidPointFields)
    for row in cursor:
        midPointValues = deepcopy(row[:-1])
        while None in midPointValues:
            midPointValues.remove(None)
        row[-1] = sum(midPointValues)
        cursor.updateRow(row)


def computeSeverityMidpoint(featureClass, TPAField, MidPointField):
    cursor = arcpy.da.UpdateCursor(featureClass, [TPAField, MidPointField])
    for row in cursor:
        if row[0] == 0:
            row[1] = 0
        elif row[0] > 0 and row[0] <= 10:
            row[1] = 5
        elif row[0] > 10 and row[0] <= 30:
            row[1] = 20
        elif row[0] > 30:
            row[1] = 65
        cursor.updateRow(row)


def setNegativeTPAToZero(featureClass, TPAField):
    cursor = arcpy.da.UpdateCursor(featureClass, TPAField)
    for row in cursor:
        if row[0] == -1:
            row[0] = 1
        elif row[0] < 0 and row[0] != -1:
            row[0] = row[0] * -1
        cursor.updateRow(row)


def populateHOSTCODEWithMostCommon(featureClass):
    hostFields = [field.name for field in arcpy.ListFields(featureClass) if 'HOST' in field.name]
    hostFields.remove('HOST_CODE')
    hostFields.append('HOST_CODE')
    cursor = arcpy.da.UpdateCursor(featureClass, hostFields)
    for row in cursor:
        values = row[:]
        while None in values:
            values.remove(None)
        while 0 in values:
            values.remove(0)
        while -1 in values:
            values.remove(-1)
        if values:
            counts = Counter(values)
            mostCommonHost = counts.most_common()[0][0]
            row[-1] = mostCommonHost
            cursor.updateRow(row)
        else:
            row[-1] = None
