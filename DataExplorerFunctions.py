import arcpy

def deleteUneededFields(featureClass, fieldsToKeep):
    fieldsToDelete = [
        field.name for field in arcpy.ListFields(featureClass)
        if field.name not in fieldsToKeep
        and not field.required]
    arcpy.DeleteField_management(featureClass, fieldsToDelete)


def makeEmptyADSTable(featureClass):
    tableName = 'ADS_Expanded'
    tableInMemoryPath = os.path.join('in_memory', tableName)

    arcpy.TableSelect_analysis(featureClass, tableInMemoryPath)
    arcpy.AddField_management(tableInMemoryPath, 'ORIGINAL_ID', 'LONG')
    arcpy.AddField_management(tableInMemoryPath, 'DUPLICATE', 'SHORT')
    arcpy.AddField_management(tableInMemoryPath, 'TPA', 'FLOAT')
    arcpy.AddField_management(tableInMemoryPath, 'DCA_CODE', 'LONG')
    arcpy.AddField_management(tableInMemoryPath, 'HOST', 'SHORT')
    arcpy.DeleteRows_management(tableName)
    fieldsToKeep = [
        'ORIGINAL_ID', 'DUPLICATE', 'TPA', 'DCA_CODE', 'HOST', 'ACRES'
    ]
    deleteUneededFields(tableName, fieldsToKeep)
    


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
                ['DMG_TYPE{}'.format(number),
                'DCA{}'.format(number),
                'TPA{}'.format(number)], 'DMG_TYPE{} NOT IN (1, 2)'.format(number))
        for row in cursor:
            row[0] = -1
            row[1] = 99999
            row[2] = -1
            cursor.updateRow(row)


def easyValues(featureClass, uniqueDCAValues):
    easyDict = {}
    for uD in uniqueDCAValues:
        cursor = arcpy.da.SearchCursor(
            featureClass,
            ['OBJECTID',
            'TPA1',
            'TPA2',
            'TPA3',
            'DCA1',
            'ACRES'],
            'DCA1 = {0} AND DCA2 IN (99999, {0}) AND DCA3 IN (99999, {0})'.format(uD))
        try:
            for row in cursor:
                TPAList = row[1:4]
                replaceNegList = [0 if x == -1 else x for x in TPAList]
                tpaSum = sum(replaceNegList)
                finalList = list(row[4:])
                finalList.insert(0, tpaSum)
                easyDict[row[0]] = finalList
        except:
            pass
    return easyDict


def difficultValues(featureClass, easyDict):
    diffCausDict = {}
    cursor = arcpy.da.SearchCursor(
        featureClass,
        ['DCA1',
        'DCA2',
        'DCA3',
        'TPA1',
        'TPA2',
        'TPA3',
        'ACRES',
        'OBJECTID'],
        'OBJECTID NOT IN ' + str(tuple(easyDict.keys())))

    for row in cursor:
        if row[0] == 99999:
            pass
        else:
            row = list(row)
            diffCausDict[row[-1]] = []
            # all 3 are different
            TPARowNumbers = [3, 4, 5]
            for TPARow in TPARowNumbers:
                if int(row[TPARow]) == -1:
                    row[TPARow] = 0

            if row[0] != row[1] and row[0] != row[2] and row[1] != row[2] and row[1] != 99999 and row[2] != 99999:
                finalList = [row[3], row[0], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)
                finalList = [row[4], row[1], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)
                finalList = [row[5], row[2], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)

            # first two are equal 3rd values caputured if not 99999
            if row[0] == row[1] and row[1] != row[2]:
                finalList = [row[3] + row[4], row[0], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)
                if row[2] != 99999:
                    finalList = [row[5], row[2], row[-2]]
                    diffCausDict[row[-1]].append(finalList)

            # last two are equal and first value caputured if not 99999
            if row[0] != row[1] and row[1] == row[2] and row[1] != 99999:
                finalList = [row[4] + row[5], row[1], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)
                finalList = [row[3], row[0], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)

            # first and last are equal middle value caputured if not 99999
            if row[0] != row[1] and row[0] == row[2]:
                finalList = [row[3] + row[5], row[0], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)
                if row[1] != 99999:
                    finalList = [row[4], row[1], row[-2]]
                    diffCausDict[row[-1]].append(finalList)

            # first two are not equal and last is 99999
            if row[0] != row[1] and row[2] == 99999:
                finalList = [row[3], row[0], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)
                finalList = [row[4], row[1], row[-2]]
                diffCausDict[row[-1]].append(finalList)

            # first and last not equal and middle is 99999
            if row[0] != row[2] and row[1] == 99999 and row[2] != 99999:
                finalList = [row[3], row[0], row[-2]]
                diffCausDict[row[-1]].append(finalList)
                del(finalList)
                finalList = [row[5], row[2], row[-2]]
                diffCausDict[row[-1]].append(finalList)
    return diffCausDict


def uniqueValuesFromFeatureField(featureClass, field):
    with arcpy.da.SearchCursor as cursor:
        uniqueValues = list(set(row[0] for row in cursor))
    return uniqueValues


def mtnPineHandling(featureClass, DCAValue):
    arcpy.AddField_management(featureClass "ADS_OBJECTID", 'LONG')
    arcpy.CalculateField_management(featureClass, 'ADS_OBJECTID', '!OBJECTID!', 'PYTHON', '#')
    DCADict = {}
    outputTableName = 'in_memory\\DCA{}'.format(DCAValue)
    arcpy.TableSelect_analysis(
        featureClass,
        outputTableName,
        'DCA1 = {0} OR DCA2 = {0} OR DCA3 = {0}'.format(DCAValue))

    for number in  range(1, 4):
        fields = [
            'DCA{}'.format(number),
            'TPA{}'.format(number),
            'HOST{}'.format(number)]
        cursor = arcpy.da.UpdateCursor(outputTableName, fields)
    for row in cursor:
        if row[0] != DCAValue:
            row[0] = 99999
            row[1] = -1
            row[2] = -1

    for number in range(1,4):
        fields = [
            'ADS_OBJECTID',
            'DCA{}'.format(number),
            'TPA{}'.format(number),
            'HOST{}'.format(number),
            'ACRES']

    cursor = arcpy.da.SearchCursor(outputTableName, fields)
    for row in cursor:
        if row[0] not in DCADict.keys() and row[1] == DCAValue:
            DCADict[row[0]] = []
            DCADict[row[0]].append([row[1], row[2], row[3]])
        elif row[0] in DCADict.keys() and row[1] == DCAValue:
            DCADict[row[0]].append([row[1], row[2], row[3]])
    return DCADict

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
