from arcpy.sa import *
import glob
import os
import numpy as np

#maps = glob.glob(r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R04\ADS\1964\maps\*.tif')
finalGDB = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\MapExtraction.gdb'
mapFile = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\R04\ADS\1964\maps\Saw_WSB_NDiv1964.tif'
prjFilePathWO = r'T:\FS\Reference\GeoTool\r01\Script\NRGG\WO_Alber_Projection.txt'
prjFilePathWWGS84 = r'T:\FS\Reference\GeoTool\r01\Script\NRGG\WGS4_PRJ.txt'

#for mapFile in maps:
print('Working on feature extraction from', os.path.basename(mapFile))
isoRaster = IsoClusterUnsupervisedClassification(mapFile, 3)

neighborhood = NbrRectangle(9, 9, "CELL")

# Check out the ArcGIS Spatial Analyst extension license

# Execute FocalStatistics
outFocalStatistics = FocalStatistics(isoRaster, neighborhood, "MAJORITY")
nulledRaster = SetNull(outFocalStatistics, outFocalStatistics, 'VALUE <>2')
arcpy.RasterToPolygon_conversion(
    nulledRaster, os.path.join(
        arcpy.env.workspace, 'polygonConversion'),
        'NO_SIMPLIFY', 'Value', 'SINGLE_OUTER_PART')

with open(prjFilePathWWGS84) as firstProjection:
    prjWGS = firstProjection.read()

firstProject = os.path.join(arcpy.env.workspace, 'firstProject')
arcpy.Project_management('polygonConversion', firstProject,  prjWGS)

with open(prjFilePathWO) as secondProjection:
    prjWO = secondProjection.read()

secondProject = os.path.join(arcpy.env.workspace, 'secondProject')
arcpy.Project_management('firstProject', secondProject, prjWO)


arr = arcpy.da.FeatureClassToNumPyArray('secondProject', 'SHAPE@AREA')

arr = arr.astype('float64')
p1 = np.percentile(arr, 99.97)

finalOutput = os.path.join(
    finalGDB, '{}_polygons'.format(os.path.basename(mapFile)[:-4]))
arcpy.Select_analysis(
    'secondProject', finalOutput, 'Shape_Area >= {}'.format(p1))
