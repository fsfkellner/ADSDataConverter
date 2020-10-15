import os
import arcpy
import sys
sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
# sys.path.append(r'C:\Data\ADSDataConverter')
import ADSFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
# sys.path.append(r'C:\Data')
import NRGG


topLevelFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\ADS_RS_2020'
workingFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\DecadeUnion'

featureClasses = NRGG.findAllFeatureClasses(topLevelFolder)


decadeList = [
    [1962, 1970, 'NineteenSixtiesFiles'],
    [1970, 1980, 'NineteenSeventiesFiles'],
    [1980, 1990, 'NineteenEightiesFiles'],
    [1990, 2000, 'NineteenNinetiesFiels'],
    [2000, 2010, 'TwoThousandsFiles'],
    [2010, 2016, 'TwoThousandTeensFiles']]

for decade in decadeList:
    GDBName = '{}.gdb'.format(decade[2])
    arcpy.CreateFileGDB_management(workingFolder, GDBName)
    arcpy.env.workspace = os.path.join(workingFolder, GDBName)
    decadeFilteredFeatureClasses = ADSFunctions.getDecadeFeatureClasses(
        featureClasses, decade[0], decade[1])
    DCAValuesFromDecade = ADSFunctions.getDCAValuesFromFiles(
        decadeFilteredFeatureClasses)
    for DCAValue in DCAValuesFromDecade:
        singleDCADecadeFeatureClasses = ADSFunctions.featuresInDecadeSingleDCAValue(
            decadeFilteredFeatureClasses, DCAValue)

        unionFiles = []
        for singleDCAFeatureClass in singleDCADecadeFeatureClasses[:2]:
            layerViewName = '{}_view'.format(
                os.path.basename(singleDCAFeatureClass))
            arcpy.MakeFeatureLayer_management(
                singleDCAFeatureClass, layerViewName)
            arcpy.AddField_management(layerViewName, "YEAR", 'SHORT')
            arcpy.CalculateField_management(layerViewName, "YEAR", 1)
            ADSFunctions.setNegativeTPAToZero(layerViewName, 'TPA')
            unionFiles.append(layerViewName)

        unionName = '{}_{}'.format(decade[2][:-5], DCAValue)
        unionPath = os.path.join(GDBName, unionName)
        arcpy.Union_analysis(unionFiles, unionName)
        arcpy.AddField_management(unionName, 'TPATotal', 'DOUBLE')
        arcpy.AddField_management(unionName, 'YEARTotal', 'SHORT')
        yearFields = ADSFunctions.getYearFields(unionName)
        TPAFields = ADSFunctions.getTPAFields(unionName)
        ADSFunctions.computeTotalYears(unionName, yearFields)
        ADSFunctions.computeTotalTPA(unionName, TPAFields)
        arcpy.AddField_management(unionName, 'Severity_MidPoint', 'SHORT')
        arcpy.AddField_management(unionName, "SeverityWeightedAcres", 'FLOAT')
        arcpy.AddField_management(unionName, "Acres_Mapped", 'FLOAT')
        arcpy.CalculateField_management(
            unionName, "Acres_Mapped", "!shape.area@acres!", "PYTHON_9.3")
        ADSFunctions.computeSeverityMidpoint(
            unionName, 'TPATotal', 'Severity_MidPoint')
        ADSFunctions.computeSeverityWeightedAcres(
            unionName,
            'Severity_MidPoint',
            "Acres_Mapped", "SeverityWeightedAcres")
        finaldUnionName = '{}_Final'.format(unionName)
        outputGDBPath = os.path.join(workingFolder, GDBName)
        arcpy.FeatureClassToFeatureClass_conversion(
            unionName, outputGDBPath, finaldUnionName)
        ADSFunctions.deleteUneededFields(
            finaldUnionName,
            [
                'TPATotal',
                'YEARTotal',
                'Severity_MidPoint',
                'SeverityWeightedAcres',
                'Acres_Mapped'
            ])
        arcpy.AddField_management(finaldUnionName, 'DCA_CODE', 'LONG')
        arcpy.CalculateField_management(
            finaldUnionName, 'DCA_CODE', DCAValue, "PYTHON_9.3")
