import os
import arcpy
import sys
import glob

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG

def listFields(featureClass):
    fields = [field.name for field in arcpy.ListFields(featureClass) if not field.required]
    return fields

def getRowValues(featureClass, fields):
    valueDict = {row[0]:row[1] for row in arcpy.da.SearchCursor(featureClass, fields)}
    return valueDict

tbx = arcpy.ImportToolbox(r'T:\FS\Reference\GeoTool\r01\Toolbox\NRGGFieldCalculator\NRGGFieldCalculator.pyt' )
workingFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R04\ADS\shapefiles'
prjFilePath = r'T:\FS\Reference\GeoTool\r01\Script\FSVeg\WO_Alber_Projection.txt'

shapefiles = glob.glob(os.path.join(workingFolder, '*dmg.shp'))
outPutFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R4_ADS_Data'

fieldsThatShouldBeCaps = [
            ['DCA', 'LONG'],
            ['TPA', 'FLOAT'],
            ['HOST', 'SHORT'],
            ['DMG_TYPE', 'SHORT']
            ]
# get WO FHP projection
with open(prjFilePath) as prjFile:
    prj = prjFile.read()

for shapefile in shapefiles:
    year = ADSFunctions.findDigits(os.path.basename(shapefile))[1:]
    year = NRGG.listStringJoiner(year, '')

    os.mkdir(os.path.join(outPutFolder,  str(year)))
    yearFolderPath = os.path.join(outPutFolder,  str(year))
    GDBName = 'R4ADS{}'.format(year)
    outPutGDB = ADSFunctions.makeNewGDBIfDoesntExist(yearFolderPath, GDBName)
    newFileName = 'R4ADS{}Damage'.format(year)
    outPath = os.path.join(outPutGDB, newFileName)
    arcpy.Project_management(shapefile, outPath, prj)
    fileFields = listFields(newFileName)
    if 'DCA1' in fileFields:
        pass
    else:
        for field in fieldsThatShouldBeCaps:
            for i in range(1, 4):
                newField = '{}{}'.format(field[0], i)
                updateDict = getRowValues(newFileName, ['OBJECTID', newField.lower()])
                arcpy.DeleteField_management(newFileName, newField.lower())
                arcpy.AddField_management(newFileName, newField, field[1])
                cursor = arcpy.da.UpdateCursor(newFileName, ['OBJECTID', newField])
                for row in cursor:
                    if row[0] in updateDict:
                        row[1] = updateDict[row[0]]
                        cursor.updateRow(row)

        updateDict = getRowValues(newFileName, ['OBJECTID', 'acres'])
        arcpy.DeleteField_management(newFileName, 'acres')
        arcpy.AddField_management(newFileName, 'ACRES', 'FLOAT')
        cursor = arcpy.da.UpdateCursor(newFileName, ['OBJECTID', 'ACRES'])
        for row in cursor:
            if row[0] in updateDict:
                row[1] = updateDict[row[0]]
                cursor.updateRow(row)
