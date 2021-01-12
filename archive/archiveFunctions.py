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
    and expanded single DCA table.
    '''
    arcpy.SelectLayerByAttribute_management(featureClass, "CLEAR_SELECTION")
    arcpy.SelectLayerByAttribute_management(featureClass, "NEW_SELECTION", whereStatement)
    count = int(arcpy.GetCount_management(featureClass)[0])
    arcpy.SelectLayerByAttribute_management(featureClass, "CLEAR_SELECTION")
    if count > 0:
        return True
    else:
        return False


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


def sumMidPoints(featureClass, fieldsList):
    cursor = arcpy.da.UpdateCursor(featureClass, fieldsList)
    for row in cursor:
        midPointValues = deepcopy(row[:-1])
        while None in midPointValues:
            midPointValues.remove(None)
        row[-1] = sum(midPointValues)
        cursor.updateRow(row)

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