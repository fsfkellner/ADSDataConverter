import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Union MultiYear ExpandedADS Data"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [UnionMultiYearExpandedADSData, CreateSingleDCAFeatureClasses]


class UnionMultiYearExpandedADSData(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Union MultiYear ExpandedADS Data"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName='Geodatabase Where Existing Single Causal Agent ADS Files are Located',
            name='Location of Existing Files',
            datatype='GPString',
            parameterType="Required",
            direction="Input")
        
        param0.filter.list = ["Default GDB", "Jess' GDB", "Jeff's GDB", "Andrew's GDB"]
        
        #param0.value = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\Merged_Historic_ADS_Data.gdb'

        param1 = arcpy.Parameter(
            displayName='Geodatabase Where Files Will Be Written',
            name='Geodatabse for output files',
            datatype='DEWorkspace',
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName='Analysis Start Year',
            name='Year which analysis will begin',
            datatype='GPstring',
            parameterType="Required",
            direction="Input")

        param2.filter.list = range(1962, 2015)

        param3 = arcpy.Parameter(
            displayName='Analysis End Year',
            name='Year which analysis will end',
            datatype='GPstring',
            parameterType="Required",
            direction="Input")

        param3.filter.list = range(1963, 2016)

        param4 = arcpy.Parameter(
            displayName='DCA Value',
            name='DCA Value',
            datatype='GPstring',
            multiValue=True,
            parameterType="Optional",
            direction="Input")

        param4.filter.list = [11000, 11002, 11006, 11007, 11009, 11015, 11029, 11049, 11050, 11900, 12000, 12003, 12011, 12014, 12015, 12037, 12039, 12040, 12047, 12049, 12080, 12083, 12096, 12104, 12116, 12117, 12123, 12128, 12139, 12146, 12159, 12160, 12203, 12900, 14003, 14039, 14040, 19000, 21000, 21001, 21017, 22057, 23001, 23011, 23023, 24008, 25000, 25002, 25005, 25022, 25028, 25033, 25034, 25035, 25039, 25050, 25058, 25062, 25074, 26001, 26002, 26004, 30000, 30001, 41000, 50002, 50003, 50004, 50005, 50006, 50011, 50012, 50013, 50014, 50015, 50017, 50800, 70000, 80002, 90000, 90008, 90009, 90010]
        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[2].value:
            startValue = int(parameters[2].value) + 1
            parameters[3].filter.list = range(startValue, 2016)

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import os
        import arcpy
        import sys
        sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
        import ADSFunctions

        sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
        import NRGG

        topLevelFolder = parameters[0].valueAsText

        outPutGDB = parameters[1].valueAsText
        startYear = int(parameters[2].valueAsText)
        endYear = int(parameters[3].valueAsText)
        DCAValuesFromDecade = parameters[4].values

        GDBDict = {
            "Default GDB" : r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\Merged_Historic_ADS_Data.gdb',
            "Jess' GDB" : r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\Missoula\GIS\Workspace\JJenne\R1_Union\Merged_Historic_ADS_Data.gdb',
            "Jeff's GDB" : r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\Missoula\GIS\Workspace\JKaiden\R1_Historic_ADS_data\Merged_Historic_ADS_Data.gdb',
            "Andrew's GDB" : r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\CoeurdAlene\GIS\Workspace\arichards\ADS_UnionProject_2020\RichardsMerged_Historic_ADS_Data.gdb'
        }
        topLevelFolder = GDBDict[topLevelFolder]
        #with open(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions\expandedADSFeatureClasses.txt') as text:
        #    featureClasses = [t.strip('\n') for t in text.readlines()]
        featureClassText = open(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions\R1_Expanded_ADS_FeatureClasses.txt', 'r')
        featureClasses = [os.path.join(topLevelFolder, featureClass.strip('\n')) for featureClass in featureClassText.readlines()]
        featureClassText.close()
        #featureClasses = NRGG.findAllFeatureClasses(topLevelFolder)

        GDBName = os.path.basename(outPutGDB)
        workingFolder = os.path.dirname(outPutGDB)
        arcpy.env.workspace = os.path.join(
            workingFolder, GDBName)
        decadeFilteredFeatureClasses = ADSFunctions.getDecadeFeatureClasses(
            featureClasses, startYear, endYear + 1)
        if DCAValuesFromDecade is None:
            DCAValuesFromDecade = ADSFunctions.getDCAValuesFromFiles(
                decadeFilteredFeatureClasses)
        else:
            DCAValuesFromDecade = [int(DCAValue) for DCAValue in DCAValuesFromDecade]

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
            if not unionFiles:
                message = 'DCA Value {} is not present within the time period you selected. No Union will be performed'.format(DCAValue)
                arcpy.AddMessage(message)
            else:
                unionFiles.sort()
                arcpy.AddMessage(unionFiles)
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
                arcpy.AddField_management(unionName, 'HOST_CODE', 'SHORT')
                arcpy.CalculateField_management(
                    unionName, "Acres_Mapped", "!shape.area@acres!", "PYTHON_9.3")
                ADSFunctions.computeSeverityMidpoint(
                    unionName, 'TPATotal', 'Severity_MidPoint')
                ADSFunctions.computeSeverityWeightedAcres(
                    unionName,
                    'Severity_MidPoint',
                    "Acres_Mapped", "SeverityWeightedAcres")
                ADSFunctions.populateHOSTCODEWithMostCommon(unionName)
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
                        'Acres_Mapped',
                        'HOST_CODE'
                    ])
                arcpy.AddField_management(finaldUnionName, 'DCA_CODE', 'LONG')
                arcpy.CalculateField_management(
                    finaldUnionName, 'DCA_CODE', DCAValue, "PYTHON_9.3")


class CreateSingleDCAFeatureClasses(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Make Single DCA Value Feature Classes"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):

        param10 = arcpy.Parameter(
            displayName='Geodatabase Where Files Will Be Written',
            name='Geodatabse for output files',
            datatype='DEWorkspace',
            parameterType="Required",
            direction="Input")

        param11 = arcpy.Parameter(
            displayName='Analysis Start Year',
            name='Year which analysis will begin',
            datatype='GPstring',
            parameterType="Required",
            direction="Input")

        param11.filter.list = range(1962, 2019)

        param12 = arcpy.Parameter(
            displayName='Analysis End Year',
            name='Year which analysis will end',
            datatype='GPstring',
            parameterType="Required",
            direction="Input")

        param12.filter.list = range(1963, 2020)

        param13 = arcpy.Parameter(
            displayName='DCA Value',
            name='DCA Value',
            datatype='GPstring',
            multiValue=True,
            parameterType="Required",
            direction="Input")
        
        param13.filter.list = [11000, 11002, 11006, 11007, 11009, 11015, 11029, 11049, 11050, 11900, 12000, 12003, 12011, 12014, 12015, 12037, 12039, 12040, 12047, 12049, 12080, 12083, 12096, 12104, 12116, 12117, 12123, 12128, 12139, 12146, 12159, 12160, 12203, 12900, 14003, 14039, 14040, 19000, 21000, 21001, 21017, 22057, 23001, 23011, 23023, 24008, 25000, 25002, 25005, 25022, 25028, 25033, 25034, 25035, 25039, 25050, 25058, 25062, 25074, 26001, 26002, 26004, 30000, 30001, 41000, 50002, 50003, 50004, 50005, 50006, 50011, 50012, 50013, 50014, 50015, 50017, 50800, 70000, 80002, 90000, 90008, 90009, 90010]
        
        #param14 = arcpy.Parameter(
        #    displayName='Damage Types',
        #    name='Damage Type',
        #    datatype='GPstring',
        #    multiValue=True,
        #    parameterType="Optional",
        #    direction="Input")
        #param14.filter.list = [1, 2, 3, 4, 7, 8, 10]

        params = [param10, param11, param12, param13]#, param14]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[1].value:
            startValue = int(parameters[1].value) + 1
            parameters[2].filter.list = range(startValue, 2020)

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        ########### Import statements ####################
        import os
        import arcpy
        import sys

        sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script')
        import NRGG

        sys.path.append(r'T:\FS\Reference\GeoTool\r01\Script\ADSFunctions')
        import ADSFunctions
        ###########################################################
        outPutGDBPath = parameters[0].valueAsText
        topLevelADSFolder = r'T:\FS\NFS\R01\Program\3400ForestHealthProtection\GIS\Kellner\R1_Expanded_ADS_Tables'
        # workingFolder =  os.path.dirname(parameters[0].valueAsText)

        startYear = int(parameters[1].valueAsText)
        endYear = int(parameters[2].valueAsText)

        scratchGDB = arcpy.env.workspace
        DCAValues = parameters[3].values
        damgeCodesList = None
        region = 'R1'

        DCAValues = [int(DCAValue) for DCAValue in DCAValues]
        featureClasses = ADSFunctions.findAllFeatureClasses(
            topLevelADSFolder, 'Damage')

        decadeFilteredFeatureClasses = ADSFunctions.getDecadeCopyFeatureClasses(
            featureClasses, startYear, endYear + 1)

        for featureClass in decadeFilteredFeatureClasses:
            layerViewName = '{}_View'.format(
                os.path.basename(featureClass.replace('_Copy', '')))
            arcpy.MakeFeatureLayer_management(featureClass, layerViewName)

            adsGDB = os.path.dirname(featureClass)
            arcpy.env.workspace = adsGDB
            for DCAValue in DCAValues:
                individualDCATables = [
                    os.path.join(adsGDB, table) for table in arcpy.ListTables(
                        '*{}*'.format(DCAValue)) if 'Copy' not in table]

                for individualTable in individualDCATables:
                    year = individualTable[-4:]
                    arcpy.AddMessage('Working on ' + table)
                    table = '{}_View'.format(os.path.basename(individualTable))
                    arcpy.MakeTableView_management(individualTable, table)
                    selectTableName = '{}_Copy'.format(
                        os.path.basename(individualTable))

                    selectTablePath = os.path.join(
                            scratchGDB, selectTableName)
                    arcpy.TableSelect_analysis(
                            table, selectTablePath, '1=1')

                    arcpy.MakeTableView_management(
                        selectTablePath, selectTableName)

                    mergedTableName = '{}_{}'.format(region, table.replace(
                        'Expanded', '').replace('_View', ''))

                    mergedTableName = ADSFunctions.mergeDuplicatesNoHost(
                        selectTableName, outPutGDBPath)

                    arcpy.MakeTableView_management(
                        os.path.join(outPutGDBPath, mergedTableName),
                        mergedTableName)

                    ids = ADSFunctions.returnAllValuesFromField(
                        mergedTableName, 'ORIGINAL_ID')

                    ids = NRGG.listStringJoiner(ids)
                    featureClassName = '{}_ADS_{}_Merged_{}'.format(region, DCAValue, year)

                    ADSFunctions.selectPolygonsFromOriginalData(
                        layerViewName, ids,
                        featureClassName, outPutGDBPath)

                    arcpy.MakeFeatureLayer_management(
                        os.path.join(outPutGDBPath, featureClassName),
                        featureClassName)

                    ADSFunctions.deleteUneededFields(
                        featureClassName, ['ADS_OBJECTID'])

                    arcpy.JoinField_management(
                        featureClassName,
                        'ADS_OBJECTID',
                        mergedTableName,
                        'ORIGINAL_ID',
                        'ORIGINAL_ID;DUPLICATE;TPA;DCA_CODE;HOST;ACRES')