import arcpy
import os
from collections import Counter
from copy import deepcopy
import sys
sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')

from NRGG import(
    listStringJoiner,
    findDigits,
    listFields
)


def makeEmptyADSTable(tableName, outputWorkspace):
    '''Makes an empty table with the appopriate fields
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


def makeCopyOfOriginalOBJECTID(featureClass):
    '''Adds a new fields "ADS_OBJECTID" so that
    single DCA values can be traced back to the original data
    '''
    arcpy.AddField_management(featureClass, "ADS_OBJECTID", 'LONG')
    arcpy.CalculateField_management(
        featureClass, 'ADS_OBJECTID', '!OBJECTID!', 'PYTHON', '#')


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


def convertNonDCAValuesToNull(inputTable, DCAValue):
    '''Converts all values in DCA1, DCA2 or DCA3 that are not
    equal to the input DCAValue to NULL or their NULL equivalent.
    The TPA and HOST fields associated with DCA1, DCA2 or DCA3 are
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


def computeADSMidPoint(featureClass, codeField, updateField):
    '''Takes codeField attribute column which contains the ADS
    values of LOW, MODERATE and HIGH and computes and assigns
    the serverity midpoint value to the input updateField
    attribute column
    '''
    cursor = arcpy.da.UpdateCursor(featureClass, [codeField, updateField])
    for row in cursor:
        if row[0] == 'LOW':
            row[1] = 5
        elif row[0] == 'MODERATE':
            row[1] = 20
        elif row[0] == 'HIGH':
            row[1] = 65
        cursor.updateRow(row)


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


def updateTablewithEveryDCARecord(tableName, everyDCARecordDict):
    '''Takes an empty table with appropriate fields added
    to it and updates so each unique DCA value
    gets a row in the input table
    '''
    cursor = arcpy.da.InsertCursor(
            tableName,
            ['ORIGINAL_ID',
                'TPA',
                'DCA_CODE',
                'HOST',
                'DMG_TYPE',
                'ACRES',
                'DUPLICATE'])

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


def computeSeverityWeightedAcres(
        featureClass, SeverityMidPointField, AcresField, SWAField):
    '''Compute severity weighted arces in an ADS feature class or table.
    Uses the inputs SeverityMidPointField and AcresField to compute a new
    value into input SWAField. The severity midPointField is divided by the
    constant value of 65 in every instance to compute the value which the acres
    will be multiplied by to compute severity weighted acres
    '''
    fields = [SeverityMidPointField, AcresField, SWAField]
    cursor = arcpy.da.UpdateCursor(featureClass, fields)
    for row in cursor:
        row[2] = float((float(row[0])/65.0) * float(row[1]))
        cursor.updateRow(row)


def getDecadeFeatureClasses(listOfFeatureClasses, startYear, endYear):
    '''Takes a list of feature classes and returns
    a sorted list of only those that fall within
    the start and end year.
    '''
    decadeFilteredFeatureClasses = [
        featureClass for featureClass in listOfFeatureClasses
        if int(featureClass[-4:]) in range(startYear, endYear)]

    decadeFilteredFeatureClasses.sort()  
    return decadeFilteredFeatureClasses


def getDCAValuesFromFiles(listOfGeospatialFiles):
    '''Takes a list feature classes and returns DCA values
    that are found in the naming convention of the file.
    '''
    allDCAValues = set()
    for geospatialFile in listOfGeospatialFiles:
        DCAValue = findDigits(os.path.basename(geospatialFile[:-5]))
        #DCAValue = [character for character
        #            in os.path.basename(featureClass[:-5])
        #            if character.isdigit()]

        DCAValue = listStringJoiner(DCAValue, '')
        allDCAValues.add(int(DCAValue))

    allDCAValues = list(allDCAValues)
    allDCAValues.sort()
    return allDCAValues


def featuresInDecadeSingleDCAValue(listofFeatureClasses, inputDCAValue):
    '''Given a list of featureClasses that fall within a specific time period
    this funcition will filter out all the featureClasses from 
    the input list of featureClasses contain a specific DCA value within
    the featureClasses file naming convention
    '''
    DCAFilteredFeatureClasses = []
    for featureClass in listofFeatureClasses:
        DCAValue = findDigits(os.path.basename(featureClass)[2:-5])
        #DCAValue = [character for character
        #            in os.path.basename(featureClass)[2:-5]
        #            if character.isdigit()]

        DCAValue = listStringJoiner(DCAValue, '')
        DCAValue = int(DCAValue)
        if DCAValue == inputDCAValue:
            DCAFilteredFeatureClasses.append(featureClass)

    DCAFilteredFeatureClasses.sort()
    return DCAFilteredFeatureClasses


def sumValuesAcrossSimilarFields(featureClass, listOfSimilarFields):
    '''Sums the value of similar fields within a featureClass. An
    input list of fields is provided and it is assumed the last value in the
    list is the field in which the summed valued will be calculated into.
    '''
    cursor = arcpy.da.UpdateCursor(featureClass, listOfSimilarFields)
    for row in cursor:
        valuesToSum = deepcopy(row[:-1])
        while None in valuesToSum:
            valuesToSum.remove(None)
        row[-1] = sum(valuesToSum)
        cursor.updateRow(row)


def computeSeverityMidpoint(featureClass, TPAField, midPointField):
    '''Uses the TPA field to compute a severity midpoint value into
    the input midPointField using the following classes
    TPA == 0 returns: 0
    TPA > 0 and <= 10 returns: 10
    TPA > 10 and <= 10 returns: 30
    TPA > 30 returns: 65
    '''
    cursor = arcpy.da.UpdateCursor(featureClass, [TPAField, midPointField])
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
    '''Finds instances in the ADS data table where the TPA
    value is equal to -1 and sets the TPA value to 1
    or if the value is less than zero but does not equal
    -1 the returned value to the TPA field is the negative value
    multiplied by -1
    '''
    cursor = arcpy.da.UpdateCursor(featureClass, TPAField)
    for row in cursor:
        if row[0] == -1:
            row[0] = 1
        elif row[0] < 0 and row[0] != -1:
            row[0] = row[0] * -1
        cursor.updateRow(row)


def populateHOSTCODEWithMostCommon(featureClass):
    '''Finds all of the fields with the word HOST in them 
    and then computes the most common value into an existing field 
    in the table entitled "HOST_CODE"
    '''
    hostFields = listFields(featureClass, 'HOST')
    #hostFields = [field.name for field in arcpy.ListFields(featureClass) if 'HOST' in field.name]

    # ensures that the 'HOST_CODE' fields is the end of the list and the most common
    # value will be computed into that field.
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
            # a list of tuples is returned with most_common [0][0] grabs the first element value 
            mostCommonHost = counts.most_common()[0][0]
            row[-1] = mostCommonHost
            cursor.updateRow(row)
        else:
            row[-1] = None
