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
