import math
import statistics
from typing import Tuple, Optional, Dict
from src.kernel.buffer import BufferManager

class ZScoreEngine:
    """
    Anomaly detection using Standard Score (Z-Score).
    Flags values that are > 3 standard deviations from the mean.
    """
    def __init__(self, window_size: int = 60, threshold: float = 3.0):
        self.buffer = BufferManager(maxlen=window_size)
        self.threshold = threshold

    def process(self, value: float) -> Dict[str, any]:
        """
        Ingest value and return analysis.
        :return: Dict with z_score and anomaly status
        """
        self.buffer.add(value)
        
        # Need at least 3 points to compute meaningful stats
        if self.buffer.size < 3:
            return {"z_score": 0.0, "anomaly": False, "msg": "insufficient_data"}

        data = self.buffer.get_all()
        try:
            mean = statistics.mean(data)
            stdev = statistics.stdev(data)
            
            if stdev == 0:
                return {"z_score": 0.0, "anomaly": False, "msg": "stable"}

            z_score = (value - mean) / stdev
            is_anomaly = abs(z_score) > self.threshold

            return {
                "z_score": round(z_score, 3),
                "anomaly": is_anomaly,
                "mean": round(mean, 3)
            }
        except Exception as e:
            return {"z_score": 0.0, "anomaly": False, "error": str(e)}

class LinearDiagnostic:
    """
    Simple Linear Regression to determine trend (slope).
    Used for HVAC performance validation.
    """
    def __init__(self, window_size: int = 15):
        self.buffer = BufferManager(maxlen=window_size)

    def process(self, value: float) -> float:
        """
        Add value and calculate slope.
        assumes processed at regular intervals (x = 0, 1, 2...)
        :return: slope (m)
        """
        self.buffer.add(value)
        if self.buffer.size < 2:
            return 0.0

        y = self.buffer.get_all()
        n = len(y)
        x = list(range(n))

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x_sq = sum(xi ** 2 for xi in x)

        denominator = (n * sum_x_sq) - (sum_x ** 2)
        if denominator == 0:
            return 0.0

        slope = ((n * sum_xy) - (sum_x * sum_y)) / denominator
        return round(slope, 4)

class SolarDiagnostic:
    """
    Passive diagnostic for light sensors using Grena algorithm approximation.
    Validates if sensor is reporting logic-defying values (e.g. dark at noon).
    """
    @staticmethod
    def calculate_elevation(lat: float, lon: float, utc_hour: float, day_of_year: int) -> float:
        """
        Simplified solar elevation calculation.
        Note: This is a simplified implementation for diagnostic purposes, 
        not for astronomical precision.
        """
        # Declination of the sun
        declination = 23.45 * math.sin(math.radians(360/365 * (day_of_year - 81)))
        
        # Equation of time
        b = math.radians(360/364 * (day_of_year - 81))
        eot = 9.87 * math.sin(2*b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
        
        # Solar time
        local_time_offset = (lon / 15.0) 
        solar_time = utc_hour + local_time_offset + (eot / 60.0)
        
        # Hour angle
        hour_angle = 15.0 * (solar_time - 12.0)
        
        # Elevation
        lat_rad = math.radians(lat)
        decl_rad = math.radians(declination)
        ha_rad = math.radians(hour_angle)
        
        sin_elev = (math.sin(lat_rad) * math.sin(decl_rad) + 
                    math.cos(lat_rad) * math.cos(decl_rad) * math.cos(ha_rad))
        
        elevation = math.degrees(math.asin(max(-1, min(1, sin_elev))))
        return round(elevation, 2)

    @staticmethod
    def validate_sensor(lux: float, elevation: float) -> bool:
        """
        Returns True if sensor is VALID, False if SUSPECT.
        Rule: If sun is high (>10 deg) and lux is near zero (<10), sensor is suspect.
        """
        if elevation > 10.0 and lux < 10.0:
            return False # Fault detected
        return True
