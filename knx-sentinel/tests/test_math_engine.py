import unittest
from src.kernel.math_engine import ZScoreEngine, LinearDiagnostic, SolarDiagnostic
from src.kernel.buffer import BufferManager

class TestBufferManager(unittest.TestCase):
    def test_circular_buffer(self):
        buf = BufferManager(maxlen=3)
        buf.add(1)
        buf.add(2)
        buf.add(3)
        self.assertEqual(buf.get_all(), [1, 2, 3])
        
        buf.add(4)
        self.assertEqual(buf.get_all(), [2, 3, 4]) # 1 should be evicted

class TestZScoreEngine(unittest.TestCase):
    def test_stable_detection(self):
        engine = ZScoreEngine(window_size=10, threshold=2.0)
        # Feed stable data
        for _ in range(10):
            engine.process(100.0)
            
        result = engine.process(100.0)
        self.assertFalse(result["anomaly"])
        self.assertEqual(result["z_score"], 0.0)

    def test_anomaly_detection(self):
        engine = ZScoreEngine(window_size=10, threshold=3.0)
        # Feed stable data logic sequence
        stable_values = [10, 10, 10, 10, 10, 10, 10, 10, 10]
        for v in stable_values:
            engine.process(v)
            
        # Inject spike. Standard dev of [10...10] is 0. 
        # But if we have varied data:
        varied_values = [10, 12, 10, 11, 10, 12, 10, 11] # Mean ~10.75, Stdev ~0.88
        engine = ZScoreEngine(window_size=10, threshold=2.0)
        for v in varied_values:
            engine.process(v)
            
        # Z = (20 - 10.75) / 0.88 = ~10.5 > 2.0
        result = engine.process(20.0)
        self.assertTrue(result["anomaly"])
        self.assertGreater(result["z_score"], 2.0)

class TestLinearDiagnostic(unittest.TestCase):
    def test_slope_calculation(self):
        diag = LinearDiagnostic(window_size=5)
        # y = 2x, expect slope ~2.0
        # sequence: 0, 2, 4, 6, 8
        values = [0, 2, 4, 6, 8]
        for v in values:
            m = diag.process(v)
            
        self.assertAlmostEqual(m, 2.0, places=1)

    def test_flat_slope(self):
        diag = LinearDiagnostic(window_size=5)
        for _ in range(5):
            m = diag.process(10)
        self.assertEqual(m, 0.0)

class TestSolarDiagnostic(unittest.TestCase):
    def test_valid_conditions(self):
        # Elevation high (45), Lux high (1000) -> OK
        self.assertTrue(SolarDiagnostic.validate_sensor(1000, 45.0))
        
        # Elevation low (5), Lux low (0) -> OK (night)
        self.assertTrue(SolarDiagnostic.validate_sensor(0, 5.0))

    def test_fault_condition(self):
        # Elevation high (20), Lux low (5) -> Fault (covered sensor)
        self.assertFalse(SolarDiagnostic.validate_sensor(5, 20.0))

if __name__ == '__main__':
    unittest.main()
