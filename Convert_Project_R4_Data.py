import os
import arcpy
import sys
glob

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG

workingFolder = ''
prjFilePath = r'T:\FS\Reference\GeoTool\r01\Script\FSVeg\WO_Alber_Projection.txt'

shapefiles = glob.glob()

# get WO FHP projection 
with open(prjFilePath) as prjFile:
    prj = prjFile.read()

for shapefile in shapefiles:
    year = ADSFunctions.findDigits(layerViewName)[1:]
    year = NRGG.listStringJoiner(year, '')

    yearFolderPath = os.mkdir(os.path.join(workingFolder,  str(year))
    GDBName = 'R1ADS{}'.format(year)
    outPutGDB = ADSFunctions.makeNewGDBIfDoesntExist(yearFolderPath, GDBName)
    outPath = os.path.join(outPutGDB, 'R4ADS{}Damage'.format(year))
    arcpy.Project_management(shapefile, outPath, prj)