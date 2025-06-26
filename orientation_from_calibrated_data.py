#!/usr/bin/env python3
"""
ICM20948 Orientation Calculator using Calibrated Data
Calculates yaw, pitch, roll using calibrated sensor data (no EKF)

Data Flow:
Raw Sensor → Apply Calibration → NED Transform → Calculate Orientation
"""

import time
import math
import json
import sys
import numpy as np
import select
from datetime import datetime

try:
    from icm20948_ned_corrected import ICM20948_NED_Corrected
except ImportError:
    print("ERROR: Could not import ICM20948_NED_Corrected")
    print("Make sure icm20948_ned_corrected.py is in the same directory")
    sys.exit(1)

class CalibratedOrientationCalculator:
    """Calculate orientation using properly calibrated sensor data"""
    
    def __init__(self, calibration_file="icm20948_raw_calibration.json"):
        self.imu = None
        self.calibration_data = None
        self.calibration_file = calibration_file
        
        # Integration state for gyroscope
        self.gyro_roll = 0.0
        self.gyro_pitch = 0.0
        self.gyro_yaw = 0.0
        self.last_time = None
        self.gyro_initialized = False
        
        # Magnetic declination (adjust for your location)
        # Example: For most of US, declination is between -20° to +20°
        self.magnetic_declination = 0.0  # degrees, adjust for your location
        
    def initialize(self):
        """Initialize sensor and load calibration data"""
        print("🔧 Initializing ICM20948 and loading calibration...")
        
        # Initialize sensor
        try:
            self.imu = ICM20948_NED_Corrected()
            print("✅ ICM20948 initialized")
        except Exception as e:
            print(f"❌ Failed to initialize sensor: {e}")
            return False
        
        # Load calibration data
        try:
            with open(self.calibration_file, 'r') as f:
                self.calibration_data = json.load(f)
            print(f"✅ Calibration data loaded from {self.calibration_file}")
            
            # Verify it's raw calibration data
            coord_system = self.calibration_data.get('coordinate_system', 'unknown')
            if coord_system != 'raw_sensor_coordinates':
                print(f"⚠️  WARNING: Expected raw_sensor_coordinates, got {coord_system}")
                print("   Make sure you're using icm20948_raw_calibration.json")
                print("   Run: python3 calibrate_raw_sensors.py")
                
        except FileNotFoundError:
            print(f"❌ Calibration file {self.calibration_file} not found")
            print("   Run: python3 calibrate_raw_sensors.py")
            return False
        except Exception as e:
            print(f"❌ Failed to load calibration: {e}")
            return False
        
        return True
    
    def apply_calibration_and_transform(self):
        """Read raw sensors, apply calibration, transform to NED"""
        
        # Step 1: Read RAW sensor data
        accel_raw = self.imu.read_accelerometer_raw()
        gyro_raw = self.imu.read_gyroscope_raw()
        mag_raw_x, mag_raw_y, mag_raw_z, mag_valid = self.imu.read_magnetometer_raw()
        
        # Step 2: Convert to physical units
        accel_raw_g = [x * self.imu.accel_scale for x in accel_raw]
        gyro_raw_dps = [x * self.imu.gyro_scale for x in gyro_raw]
        mag_raw_ut = [mag_raw_x * self.imu.mag_scale, 
                      mag_raw_y * self.imu.mag_scale, 
                      mag_raw_z * self.imu.mag_scale] if mag_valid else [0, 0, 0]
        
        # Step 3: Apply calibration corrections (if available)
        accel_calibrated = self.apply_accel_calibration(accel_raw_g)
        gyro_calibrated = self.apply_gyro_calibration(gyro_raw_dps)
        mag_calibrated = self.apply_mag_calibration(mag_raw_ut) if mag_valid else [0, 0, 0]
        
        # Step 4: Transform to NED coordinates
        accel_ned = self.transform_accel_to_ned(accel_calibrated)
        gyro_ned = self.transform_gyro_to_ned(gyro_calibrated)
        mag_ned = self.transform_mag_to_ned(mag_calibrated) if mag_valid else [0, 0, 0]
        
        return accel_ned, gyro_ned, mag_ned, mag_valid
    
    def apply_accel_calibration(self, raw_accel):
        """Apply accelerometer calibration (bias removal and scale correction)"""
        if 'accelerometer' not in self.calibration_data:
            return raw_accel
        
        cal = self.calibration_data['accelerometer']
        bias = cal.get('bias_raw', [0, 0, 0])
        scale = cal.get('scale_factors', [1, 1, 1])
        
        # Apply bias correction and scale factors
        calibrated = [
            (raw_accel[0] - bias[0]) * scale[0],
            (raw_accel[1] - bias[1]) * scale[1],
            (raw_accel[2] - bias[2]) * scale[2]
        ]
        
        return calibrated
    
    def apply_gyro_calibration(self, raw_gyro):
        """Apply gyroscope calibration (bias removal)"""
        if 'gyroscope' not in self.calibration_data:
            return raw_gyro
        
        cal = self.calibration_data['gyroscope']
        bias = cal.get('bias_raw', [0, 0, 0])
        
        # Apply bias correction
        calibrated = [
            raw_gyro[0] - bias[0],
            raw_gyro[1] - bias[1],
            raw_gyro[2] - bias[2]
        ]
        
        return calibrated
    
    def apply_mag_calibration(self, raw_mag):
        """Apply magnetometer calibration (hard/soft iron correction)"""
        if 'magnetometer' not in self.calibration_data:
            return raw_mag
        
        cal = self.calibration_data['magnetometer']
        hard_iron = cal.get('hard_iron_offset_raw', [0, 0, 0])
        soft_iron = cal.get('soft_iron_scale_raw', [1, 1, 1])
        
        # Apply hard iron (offset) and soft iron (scale) corrections
        calibrated = [
            (raw_mag[0] - hard_iron[0]) * soft_iron[0],
            (raw_mag[1] - hard_iron[1]) * soft_iron[1],
            (raw_mag[2] - hard_iron[2]) * soft_iron[2]
        ]
        
        return calibrated
    
    def transform_accel_to_ned(self, calibrated_accel):
        """Transform calibrated accelerometer to NED coordinates"""
        # Based on your sensor mounting and test results:
        # X_ned = +X_sensor (RIGHT → North)
        # Y_ned = +Y_sensor (FORWARD → East)  
        # Z_ned = -Z_sensor (UP → Down)
        return [
            +calibrated_accel[0],  # North
            +calibrated_accel[1],  # East
            -calibrated_accel[2]   # Down
        ]
    
    def transform_gyro_to_ned(self, calibrated_gyro):
        """Transform calibrated gyroscope to NED coordinates"""
        # Based on your sensor mounting and test results:
        # X_ned = -X_sensor (RIGHT rotation → North, negated)
        # Y_ned = -Y_sensor (FORWARD rotation → East, negated)
        # Z_ned = +Z_sensor (UP rotation → Down, no negation)
        return [
            -calibrated_gyro[0],  # North
            -calibrated_gyro[1],  # East
            +calibrated_gyro[2]   # Down
        ]
    
    def transform_mag_to_ned(self, calibrated_mag):
        """Transform calibrated magnetometer to NED coordinates"""
        # Based on your sensor mounting and test results:
        # X_ned = -X_sensor (RIGHT direction → North, negated)
        # Y_ned = -Y_sensor (FORWARD direction → East, negated)
        # Z_ned = -Z_sensor (UP → Down, negated)
        return [
            -calibrated_mag[0],  # North
            -calibrated_mag[1],  # East  
            -calibrated_mag[2]   # Down
        ]
    
    def calculate_accel_orientation(self, accel_ned):
        """Calculate roll and pitch from accelerometer (NED coordinates)"""
        ax, ay, az = accel_ned
        
        # Calculate roll and pitch from gravity vector
        # In NED: X=North, Y=East, Z=Down
        # Roll: rotation around North axis (X)
        # Pitch: rotation around East axis (Y)
        
        # Roll (bank angle) - positive when right wing down
        roll = math.atan2(ay, math.sqrt(ax*ax + az*az))
        
        # Pitch (elevation angle) - positive when nose up
        pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az))
        
        # Convert to degrees
        roll_deg = math.degrees(roll)
        pitch_deg = math.degrees(pitch)
        
        return roll_deg, pitch_deg
    
    def calculate_mag_yaw(self, mag_ned, accel_ned):
        """Calculate yaw from magnetometer with tilt compensation"""
        mx, my, mz = mag_ned
        ax, ay, az = accel_ned
        
        # First calculate roll and pitch for tilt compensation
        roll_rad = math.atan2(ay, math.sqrt(ax*ax + az*az))
        pitch_rad = math.atan2(-ax, math.sqrt(ay*ay + az*az))
        
        # Tilt compensation for magnetometer
        # Compensate for roll and pitch to get true magnetic heading
        cos_roll = math.cos(roll_rad)
        sin_roll = math.sin(roll_rad)
        cos_pitch = math.cos(pitch_rad)
        sin_pitch = math.sin(pitch_rad)
        
        # Tilt-compensated magnetic field components
        mag_x_comp = mx * cos_pitch + mz * sin_pitch
        mag_y_comp = mx * sin_roll * sin_pitch + my * cos_roll - mz * sin_roll * cos_pitch
        
        # Calculate magnetic heading (corrected for NED convention)
        # In NED: positive yaw = clockwise when viewed from above
        yaw_rad = math.atan2(mag_y_comp, mag_x_comp)  # Removed negative sign
        yaw_deg = math.degrees(yaw_rad)
        
        # Apply magnetic declination correction
        yaw_deg += self.magnetic_declination
        
        # Normalize to 0-360°
        if yaw_deg < 0:
            yaw_deg += 360
        elif yaw_deg >= 360:
            yaw_deg -= 360
        
        return yaw_deg
    
    def integrate_gyro(self, gyro_ned, dt, accel_roll=None, accel_pitch=None, mag_yaw=None):
        """Integrate gyroscope for orientation with initialization and bias correction"""
        if dt <= 0:
            return self.gyro_roll, self.gyro_pitch, self.gyro_yaw
        
        # Initialize gyro integration with accelerometer values on first call
        if not self.gyro_initialized and accel_roll is not None and accel_pitch is not None:
            self.gyro_roll = accel_roll
            self.gyro_pitch = accel_pitch
            if mag_yaw is not None:
                self.gyro_yaw = mag_yaw
            self.gyro_initialized = True
            print(f"📍 Gyro integration initialized: Roll={self.gyro_roll:.1f}°, Pitch={self.gyro_pitch:.1f}°, Yaw={self.gyro_yaw:.1f}°")
            return self.gyro_roll, self.gyro_pitch, self.gyro_yaw
        
        # Integrate angular rates
        self.gyro_roll += gyro_ned[0] * dt    # Roll rate around North axis
        self.gyro_pitch += gyro_ned[1] * dt   # Pitch rate around East axis  
        self.gyro_yaw += gyro_ned[2] * dt     # Yaw rate around Down axis
        
        # Apply simple drift correction (optional)
        # Slowly pull gyro towards accelerometer values when motion is low
        if accel_roll is not None and accel_pitch is not None:
            gyro_magnitude = math.sqrt(gyro_ned[0]**2 + gyro_ned[1]**2 + gyro_ned[2]**2)
            if gyro_magnitude < 2.0:  # Low motion, apply gentle correction
                correction_factor = 0.001  # Very gentle correction
                self.gyro_roll += (accel_roll - self.gyro_roll) * correction_factor
                self.gyro_pitch += (accel_pitch - self.gyro_pitch) * correction_factor
        
        # Keep angles in reasonable ranges
        self.gyro_roll = self.normalize_angle_180(self.gyro_roll)
        self.gyro_pitch = self.normalize_angle_180(self.gyro_pitch)
        self.gyro_yaw = self.normalize_angle_360(self.gyro_yaw)
        
        return self.gyro_roll, self.gyro_pitch, self.gyro_yaw
    
    def reset_gyro_integration(self, accel_roll, accel_pitch, mag_yaw=None):
        """Reset gyro integration to match absolute sensor values"""
        self.gyro_roll = accel_roll
        self.gyro_pitch = accel_pitch
        if mag_yaw is not None:
            self.gyro_yaw = mag_yaw
        self.gyro_initialized = True
        print(f"🔄 Gyro integration reset: Roll={self.gyro_roll:.1f}°, Pitch={self.gyro_pitch:.1f}°, Yaw={self.gyro_yaw:.1f}°")
    
    def check_user_input(self):
        """Check for user input without blocking"""
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.readline().strip().lower()
        return None
    
    def normalize_angle_180(self, angle):
        """Normalize angle to [-180, 180] degrees"""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle
    
    def normalize_angle_360(self, angle):
        """Normalize angle to [0, 360] degrees"""
        while angle >= 360:
            angle -= 360
        while angle < 0:
            angle += 360
        return angle
    
    def run_orientation_calculation(self):
        """Main loop for real-time orientation calculation"""
        print("\n🧭 ICM20948 Calibrated Orientation Calculator")
        print("=" * 70)
        print("Using calibrated sensor data to calculate orientation")
        print("Data flow: Raw → Calibration → NED → Orientation")
        print()
        print("Controls:")
        print("  • Press Ctrl+C to stop")
        print("  • Type 'r' + Enter to reset gyro integration")
        print("  • Type 'h' + Enter to show this help")
        print()
        
        if self.calibration_data:
            cal_time = self.calibration_data.get('timestamp', 'unknown')
            print(f"📊 Using calibration from: {cal_time}")
            
            # Show calibration summary
            if 'abnormalities' in self.calibration_data:
                abnormalities = len(self.calibration_data['abnormalities'])
                if abnormalities == 0:
                    print("✅ Calibration quality: EXCELLENT (no abnormalities)")
                elif abnormalities <= 3:
                    print(f"⚠️  Calibration quality: GOOD ({abnormalities} minor issues)")
                else:
                    print(f"❌ Calibration quality: POOR ({abnormalities} issues)")
        
        print()
        print("ACCELEROMETER/GYRO    MAGNETOMETER       GYRO INTEGRATION")
        print("Roll  Pitch           Yaw (Mag)          Roll  Pitch  Yaw")
        print("(°)   (°)             (°)                (°)   (°)    (°)")
        print("-" * 70)
        
        self.last_time = time.time()
        
        try:
            while True:
                current_time = time.time()
                dt = current_time - self.last_time if self.last_time else 0
                self.last_time = current_time
                
                # Get calibrated and NED-transformed sensor data
                accel_ned, gyro_ned, mag_ned, mag_valid = self.apply_calibration_and_transform()
                
                # Calculate orientation from accelerometer
                accel_roll, accel_pitch = self.calculate_accel_orientation(accel_ned)
                
                # Calculate yaw from magnetometer (if valid)
                if mag_valid and any(mag_ned):
                    mag_yaw = self.calculate_mag_yaw(mag_ned, accel_ned)
                    mag_yaw_str = f"{mag_yaw:6.1f}"
                else:
                    mag_yaw_str = "  N/A "
                
                # Integrate gyroscope with initialization and correction
                gyro_roll, gyro_pitch, gyro_yaw = self.integrate_gyro(
                    gyro_ned, dt, accel_roll, accel_pitch, 
                    mag_yaw if mag_valid and any(mag_ned) else None
                )
                
                # Check for user input
                user_input = self.check_user_input()
                if user_input == 'r':
                    # Reset gyro integration to match accelerometer/magnetometer
                    self.reset_gyro_integration(
                        accel_roll, accel_pitch, 
                        mag_yaw if mag_valid and any(mag_ned) else None
                    )
                elif user_input == 'h':
                    print("\n📋 Controls:")
                    print("  • 'r' + Enter: Reset gyro integration")
                    print("  • 'h' + Enter: Show this help")
                    print("  • Ctrl+C: Stop program")
                    print()
                    continue
                elif user_input is not None and user_input != '':
                    print(f"\n❓ Unknown command: '{user_input}'. Type 'h' for help.\n")
                    continue
                
                # Display results
                print(f"{accel_roll:+5.1f} {accel_pitch:+5.1f}           "
                      f"{mag_yaw_str}              "
                      f"{gyro_roll:+5.1f} {gyro_pitch:+5.1f} {gyro_yaw:6.1f}", 
                      end="\r")
                
                time.sleep(0.1)  # 10Hz update rate
                
        except KeyboardInterrupt:
            print("\n\n🎯 Orientation calculation stopped!")
            
    def close(self):
        """Close sensor connection"""
        if self.imu:
            self.imu.close()

def main():
    """Main function"""
    calculator = CalibratedOrientationCalculator()
    
    try:
        if not calculator.initialize():
            print("\n❌ Failed to initialize. Make sure:")
            print("   1. ICM20948 is connected and working")
            print("   2. Calibration file exists (run calibrate_raw_sensors.py)")
            return
        
        print("\n📋 ORIENTATION CALCULATION METHODS:")
        print("✅ ACCELEROMETER: Roll and Pitch from gravity vector")
        print("✅ MAGNETOMETER:  Yaw from magnetic field (tilt-compensated)")
        print("✅ GYROSCOPE:     Integrated orientation with drift correction")
        print()
        print("💡 IMPROVEMENTS:")
        print("   • Gyro integration now initializes with accelerometer values")
        print("   • Gentle drift correction applied during low motion")
        print("   • Reset function available ('r' + Enter)")
        print("   • Proper NED yaw convention (CW positive)")
        print()
        print("💡 NOTES:")
        print("   • Accelerometer gives absolute roll/pitch but affected by motion")
        print("   • Magnetometer gives absolute yaw but affected by magnetic interference")
        print("   • Gyroscope gives smooth motion but drifts over time")
        print("   • EKF would optimally combine all three sources")
        
        calculator.run_orientation_calculation()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        calculator.close()

if __name__ == "__main__":
    main() 