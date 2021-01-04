import sys
import os
import arcpy

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
import ADSFunctions

sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
import NRGG

ADSGDB = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\SWA\R4_Merged_Historic_ADS_Data.gdb'

tables = ADSFunctions.findAllTables(ADSGDB, 'ADS')
for table in tables:
    print('Working on File', os.path.basename(table))
    ADSFunctions.setNegativeTPAToZero(table, 'TPA')
    arcpy.AddField_management(table, 'Severity_MidPoint', 'SHORT')
    arcpy.AddField_management(table, 'SeverityWeightedAcres', 'FLOAT')
    ADSFunctions.computeSeverityMidpoint(table, 'TPA', 'Severity_MidPoint')
    ADSFunctions.computeSeverityWeightedAcres(table, 'Severity_MidPoint', 'ACRES', 'SeverityWeightedAcres')
