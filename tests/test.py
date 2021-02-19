import os
import unittest
import arcpy
import sys

sys.path.append(r'C:\Data')
sys.path.append(r'C:\Data\ADSDataConverter')
from ADSFunctions import makeEmptyADSTable

arcpy.env.overwriteOutput = True
emptyTablePath = r'C:\Data\ADSDataConverter\tests\test_data.gdb\TestEmptyADSTable'
emptyTableText = 'Tables have same number of fields'
outputWorkspace = r'C:\Data\ADSDataConverter\tests\test_data.gdb'


class TestFSVegPhotoDowloadTools(unittest.TestCase):

    def test_emptyTableText(self):
        makeEmptyADSTable('UnitTestEmptyTable', outputWorkspace)
        arcpy.TableCompare_management(os.path.join(
            outputWorkspace, 'UnitTestEmptyTable'), emptyTablePath)
        self.assertIn(emptyTableText, arcpy.GetMessages())
