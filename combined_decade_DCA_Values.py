import os
import arcpy
import sys
sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')

import ADSFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG


topLevelFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\ADS_RS_2020'
inputGDB = '#'
startYear = '#' 
endYear = '#'

decadeList = range(startYear, endYear + 1)

featureClasses = NRGG.findAllFeatureClasses(topLevelFolder)

for decade in decadeList:
    arcpy.AddMessage('Working on Year {}'.format(decade))
    GDBName = os.path.basename(inputGDB)
    workingFolder = os.path.dirname(inputGDB)
    arcpy.env.workspace = os.path.join(workingFolder, GDBName)
    decadeFilteredFeatureClasses = ADSFunctions.getDecadeFeatureClasses(
        featureClasses, startYear, endYear)
    DCAValuesFromDecade = ADSFunctions.getDCAValuesFromFiles(
        decadeFilteredFeatureClasses)
    for DCAValue in DCAValuesFromDecade:
        arcpy.AddMessage(
            'Working on DCA Value {}'.format(DCAValue))
        singleDCADecadeFeatureClasses = ADSFunctions.featuresInDecadeSingleDCAValue(
            decadeFilteredFeatureClasses, DCAValue)

        unionFiles = []
        for singleDCAFeatureClass in singleDCADecadeFeatureClasses:
            layerViewName = '{}_view'.format(
                os.path.basename(singleDCAFeatureClass))
            arcpy.MakeFeatureLayer_management(
                singleDCAFeatureClass, layerViewName)
            arcpy.AddField_management(layerViewName, "YEAR", 'SHORT')
            arcpy.CalculateField_management(layerViewName, "YEAR", 1)
            ADSFunctions.setNegativeTPAToZero(layerViewName, 'TPA')
            unionFiles.append(layerViewName)

        unionName = 'ADS_{}_{}_{}'.format(startYear, endYear, DCAValue)
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
