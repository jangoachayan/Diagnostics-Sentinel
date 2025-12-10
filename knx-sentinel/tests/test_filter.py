import unittest
from src.ingestion.filter import FilterManager

class TestFilterManager(unittest.TestCase):
    def test_empty_filter(self):
        # Default: empty list. If empty, what should happen? 
        # Plan implies matched entities are processed. Empty list -> match nothing.
        fm = FilterManager([])
        self.assertFalse(fm.should_process("sensor.anything"))

    def test_exact_match(self):
        fm = FilterManager(["sensor.target", "input_boolean.test"])
        self.assertTrue(fm.should_process("sensor.target"))
        self.assertTrue(fm.should_process("input_boolean.test"))
        self.assertFalse(fm.should_process("sensor.other"))

    def test_glob_patterns(self):
        fm = FilterManager(["*knx*", "sensor.temp_?"])
        self.assertTrue(fm.should_process("sensor.knx_status"))
        self.assertTrue(fm.should_process("binary_sensor.knx_alarm"))
        self.assertTrue(fm.should_process("sensor.temp_1"))
        self.assertTrue(fm.should_process("sensor.temp_A"))
        
        self.assertFalse(fm.should_process("sensor.temp_10")) # ? matches single char
        self.assertFalse(fm.should_process("zwave.switch"))

    def test_null_entity(self):
        fm = FilterManager(["*"])
        self.assertFalse(fm.should_process(None))
        self.assertFalse(fm.should_process(""))

if __name__ == '__main__':
    unittest.main()
