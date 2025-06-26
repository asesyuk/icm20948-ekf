#!/usr/bin/env python3
"""
ICM20948 Complete Sensor Calibration Suite

⚠️  WARNING: COORDINATE SYSTEM ISSUE DETECTED ⚠️
This calibration script works with NED-transformed coordinates,
but calibration should be done on RAW sensor coordinates!

USE calibrate_raw_sensors.py INSTEAD for proper calibration!

This script is kept for reference only.
"""

import time
import sys
import math
import json
import numpy as np
from datetime import datetime

try:
    from icm20948_ned_corrected import ICM20948_NED_Corrected
except ImportError:
    print("ERROR: Could not import the corrected sensor class")
    print("Make sure icm20948_ned_corrected.py is in the same directory")
    sys.exit(1)

class ICM20948_Calibration:
    """Complete calibration suite for ICM20948"""
    
    def __init__(self):
        self.imu = None
        self.calibration_data = {
            'timestamp': datetime.now().isoformat(),
            'accelerometer': {},
            'gyroscope': {},
            'magnetometer': {},
            'abnormalities': []
        }
        
    def initialize_sensor(self):
        """Initialize the sensor"""
        print("🔧 Initializing ICM20948...")
        try:
            self.imu = ICM20948_NED_Corrected()
            print("✅ Sensor initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize sensor: {e}")
            return False
    
    def collect_static_data(self, duration=10, description=""):
        """Collect sensor data while stationary"""
        print(f"📊 Collecting {description} data for {duration} seconds...")
        print("⚠️  Keep sensor completely still!")
        
        accel_data = []
        gyro_data = []
        mag_data = []
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # Read all sensors
            accel = self.imu.read_accelerometer_ned()
            gyro = self.imu.read_gyroscope_ned()
            mag_x, mag_y, mag_z, mag_valid = self.imu.read_magnetometer_ned()
            
            accel_data.append(accel)
            gyro_data.append(gyro)
            if mag_valid:
                mag_data.append([mag_x, mag_y, mag_z])
            
            # Progress indicator
            elapsed = time.time() - start_time
            progress = int((elapsed / duration) * 20)
            bar = "█" * progress + "░" * (20 - progress)
            print(f"\r[{bar}] {elapsed:.1f}s", end="")
            
            time.sleep(0.05)  # 20Hz sampling
        
        print("\n✅ Data collection complete")
        return np.array(accel_data), np.array(gyro_data), np.array(mag_data)
    
    def collect_rotation_data(self, axis_name, duration=15):
        """Collect data while rotating around specific axis"""
        print(f"🔄 Collecting {axis_name} rotation data for {duration} seconds...")
        print(f"   Slowly rotate sensor around {axis_name} axis")
        
        accel_data = []
        gyro_data = []
        mag_data = []
        
        start_time = time.time()
        while time.time() - start_time < duration:
            accel = self.imu.read_accelerometer_ned()
            gyro = self.imu.read_gyroscope_ned()
            mag_x, mag_y, mag_z, mag_valid = self.imu.read_magnetometer_ned()
            
            accel_data.append(accel)
            gyro_data.append(gyro)
            if mag_valid:
                mag_data.append([mag_x, mag_y, mag_z])
            
            elapsed = time.time() - start_time
            progress = int((elapsed / duration) * 20)
            bar = "█" * progress + "░" * (20 - progress)
            print(f"\r[{bar}] {elapsed:.1f}s", end="")
            
            time.sleep(0.05)
        
        print("\n✅ Rotation data collection complete")
        return np.array(accel_data), np.array(gyro_data), np.array(mag_data)
    
    def calibrate_accelerometer(self):
        """Calibrate accelerometer bias and scale factors"""
        print("\n🎯 ACCELEROMETER CALIBRATION")
        print("=" * 50)
        
        # Step 1: Collect static data (level)
        input("Place sensor LEVEL on a stable surface. Press Enter...")
        accel_level, _, _ = self.collect_static_data(10, "level accelerometer")
        
        # Step 2: Collect data in 6 orientations for scale factor calibration
        orientations = [
            ("X+ up (right side up)", [1, 0, 0]),
            ("X- up (left side up)", [-1, 0, 0]),
            ("Y+ up (forward side up)", [0, 1, 0]),
            ("Y- up (back side up)", [0, -1, 0]),
            ("Z+ up (normal up)", [0, 0, -1]),  # Z is down in NED
            ("Z- up (upside down)", [0, 0, 1])
        ]
        
        orientation_data = []
        for desc, expected in orientations:
            input(f"Orient sensor: {desc}. Press Enter...")
            accel_data, _, _ = self.collect_static_data(5, f"accelerometer {desc}")
            orientation_data.append((accel_data, expected))
        
        # Analyze accelerometer data
        self.analyze_accelerometer_data(accel_level, orientation_data)
    
    def analyze_accelerometer_data(self, level_data, orientation_data):
        """Analyze accelerometer calibration data"""
        print("\n📊 Analyzing accelerometer data...")
        
        # Calculate bias (offset when level)
        bias = np.mean(level_data, axis=0)
        bias[2] += 1.0  # Subtract gravity from Z axis
        
        # Calculate noise levels
        noise = np.std(level_data, axis=0)
        
        # Analyze scale factors from 6-point calibration
        scale_factors = [1.0, 1.0, 1.0]
        linearity_errors = []
        
        for accel_data, expected in orientation_data:
            mean_reading = np.mean(accel_data, axis=0)
            corrected = mean_reading - bias
            
            # Find dominant axis
            dominant_axis = np.argmax(np.abs(expected))
            expected_value = expected[dominant_axis]
            measured_value = corrected[dominant_axis]
            
            if abs(expected_value) > 0.5:  # Valid orientation
                scale_error = abs(measured_value) - 1.0
                linearity_errors.append(scale_error)
        
        # Store calibration results
        self.calibration_data['accelerometer'] = {
            'bias': bias.tolist(),
            'noise_std': noise.tolist(),
            'scale_errors': linearity_errors,
            'max_scale_error': max(linearity_errors) if linearity_errors else 0.0
        }
        
        # Check for abnormalities
        abnormalities = []
        if max(np.abs(bias[:2])) > 0.2:  # X,Y bias > 0.2g
            abnormalities.append("Excessive X/Y accelerometer bias")
        if abs(bias[2]) > 0.2:  # Z bias > 0.2g  
            abnormalities.append("Excessive Z accelerometer bias")
        if max(noise) > 0.05:  # Noise > 0.05g
            abnormalities.append("Excessive accelerometer noise")
        if max(linearity_errors) > 0.1:  # Scale error > 10%
            abnormalities.append("Accelerometer scale factor error")
        
        self.calibration_data['abnormalities'].extend(abnormalities)
        
        # Display results
        print(f"  Bias (g):     X={bias[0]:+.3f}, Y={bias[1]:+.3f}, Z={bias[2]:+.3f}")
        print(f"  Noise (g):    X={noise[0]:.3f}, Y={noise[1]:.3f}, Z={noise[2]:.3f}")
        print(f"  Max scale error: {max(linearity_errors):.1%}" if linearity_errors else "  Scale error: N/A")
        
        if abnormalities:
            print("  ⚠️  Abnormalities detected:")
            for abnormality in abnormalities:
                print(f"     • {abnormality}")
        else:
            print("  ✅ Accelerometer calibration looks good")
    
    def calibrate_gyroscope(self):
        """Calibrate gyroscope bias and analyze noise"""
        print("\n🎯 GYROSCOPE CALIBRATION")
        print("=" * 50)
        
        # Step 1: Collect static data for bias calibration
        input("Keep sensor completely still for gyroscope bias calibration. Press Enter...")
        _, gyro_static, _ = self.collect_static_data(30, "gyroscope bias")
        
        # Step 2: Collect rotation data for scale factor verification
        print("\nCollecting rotation data for scale factor analysis...")
        
        rotation_data = {}
        for axis in ['X (roll)', 'Y (pitch)', 'Z (yaw)']:
            input(f"Prepare to rotate around {axis} axis. Press Enter...")
            _, gyro_rot, _ = self.collect_rotation_data(axis, 15)
            rotation_data[axis] = gyro_rot
        
        # Analyze gyroscope data
        self.analyze_gyroscope_data(gyro_static, rotation_data)
    
    def analyze_gyroscope_data(self, static_data, rotation_data):
        """Analyze gyroscope calibration data"""
        print("\n📊 Analyzing gyroscope data...")
        
        # Calculate bias (drift when stationary)
        bias = np.mean(static_data, axis=0)
        
        # Calculate noise and stability
        noise = np.std(static_data, axis=0)
        
        # Allan variance calculation (simplified)
        allan_dev = self.calculate_allan_deviation(static_data)
        
        # Analyze rotation responses
        rotation_ranges = {}
        for axis, data in rotation_data.items():
            ranges = np.max(data, axis=0) - np.min(data, axis=0)
            rotation_ranges[axis] = ranges
        
        # Store calibration results
        self.calibration_data['gyroscope'] = {
            'bias': bias.tolist(),
            'noise_std': noise.tolist(),
            'allan_deviation': allan_dev.tolist(),
            'rotation_ranges': {k: v.tolist() for k, v in rotation_ranges.items()}
        }
        
        # Check for abnormalities
        abnormalities = []
        if max(np.abs(bias)) > 2.0:  # Bias > 2°/s
            abnormalities.append("Excessive gyroscope bias")
        if max(noise) > 0.5:  # Noise > 0.5°/s
            abnormalities.append("Excessive gyroscope noise")
        if max(allan_dev) > 1.0:  # Allan deviation > 1°/s
            abnormalities.append("Poor gyroscope stability (Allan variance)")
        
        self.calibration_data['abnormalities'].extend(abnormalities)
        
        # Display results
        print(f"  Bias (°/s):   X={bias[0]:+.2f}, Y={bias[1]:+.2f}, Z={bias[2]:+.2f}")
        print(f"  Noise (°/s):  X={noise[0]:.2f}, Y={noise[1]:.2f}, Z={noise[2]:.2f}")
        print(f"  Allan dev:    X={allan_dev[0]:.2f}, Y={allan_dev[1]:.2f}, Z={allan_dev[2]:.2f}")
        
        if abnormalities:
            print("  ⚠️  Abnormalities detected:")
            for abnormality in abnormalities:
                print(f"     • {abnormality}")
        else:
            print("  ✅ Gyroscope calibration looks good")
    
    def calibrate_magnetometer(self):
        """Calibrate magnetometer hard/soft iron effects"""
        print("\n🎯 MAGNETOMETER CALIBRATION")
        print("=" * 50)
        
        print("Magnetometer calibration requires rotating the sensor in 3D space")
        print("to map the magnetic field sphere. This corrects for:")
        print("• Hard iron effects (magnetic offsets)")
        print("• Soft iron effects (magnetic scaling/rotation)")
        print()
        
        input("Press Enter to start magnetometer sphere mapping...")
        
        # Collect magnetometer data while rotating in 3D
        print("🔄 Rotate sensor slowly in ALL directions for 60 seconds:")
        print("  • Roll it like a ball")
        print("  • Tumble it in 3D space")
        print("  • Cover as many orientations as possible")
        
        _, _, mag_data = self.collect_rotation_data("3D magnetometer", 60)
        
        if len(mag_data) < 100:
            print("❌ Insufficient magnetometer data collected")
            return
        
        # Analyze magnetometer data
        self.analyze_magnetometer_data(mag_data)
    
    def analyze_magnetometer_data(self, mag_data):
        """Analyze magnetometer calibration data and fit sphere"""
        print("\n📊 Analyzing magnetometer data...")
        
        if len(mag_data) == 0:
            print("❌ No valid magnetometer data")
            return
        
        # Calculate basic statistics
        mean_field = np.mean(mag_data, axis=0)
        field_ranges = np.max(mag_data, axis=0) - np.min(mag_data, axis=0)
        field_strengths = np.linalg.norm(mag_data, axis=1)
        
        # Simple hard iron calibration (offset correction)
        hard_iron_offset = mean_field
        corrected_data = mag_data - hard_iron_offset
        
        # Calculate field strength statistics after correction
        corrected_strengths = np.linalg.norm(corrected_data, axis=1)
        mean_strength = np.mean(corrected_strengths)
        strength_variation = np.std(corrected_strengths)
        
        # Soft iron approximation (scale factors)
        corrected_ranges = np.max(corrected_data, axis=0) - np.min(corrected_data, axis=0)
        target_range = np.mean(corrected_ranges)
        soft_iron_scale = target_range / corrected_ranges
        
        # Store calibration results
        self.calibration_data['magnetometer'] = {
            'hard_iron_offset': hard_iron_offset.tolist(),
            'soft_iron_scale': soft_iron_scale.tolist(),
            'mean_field_strength': float(mean_strength),
            'field_strength_variation': float(strength_variation),
            'field_ranges': field_ranges.tolist(),
            'data_points': len(mag_data)
        }
        
        # Check for abnormalities
        abnormalities = []
        if max(np.abs(hard_iron_offset)) > 100:  # Large offset
            abnormalities.append("Large hard iron offset (magnetic interference)")
        if strength_variation / mean_strength > 0.3:  # >30% variation
            abnormalities.append("Large magnetic field variation (poor calibration)")
        if min(field_ranges) < 50:  # Poor axis coverage
            abnormalities.append("Insufficient magnetometer calibration coverage")
        if len(mag_data) < 500:  # Too few points
            abnormalities.append("Insufficient magnetometer calibration data")
        if mean_strength < 20 or mean_strength > 80:  # Unusual field strength
            abnormalities.append("Unusual magnetic field strength")
        
        self.calibration_data['abnormalities'].extend(abnormalities)
        
        # Display results
        print(f"  Hard iron offset (µT): X={hard_iron_offset[0]:+.1f}, Y={hard_iron_offset[1]:+.1f}, Z={hard_iron_offset[2]:+.1f}")
        print(f"  Soft iron scale:       X={soft_iron_scale[0]:.3f}, Y={soft_iron_scale[1]:.3f}, Z={soft_iron_scale[2]:.3f}")
        print(f"  Mean field strength:   {mean_strength:.1f} µT")
        print(f"  Field variation:       {strength_variation:.1f} µT ({strength_variation/mean_strength:.1%})")
        print(f"  Data points collected: {len(mag_data)}")
        
        if abnormalities:
            print("  ⚠️  Abnormalities detected:")
            for abnormality in abnormalities:
                print(f"     • {abnormality}")
        else:
            print("  ✅ Magnetometer calibration looks good")
    
    def calculate_allan_deviation(self, data):
        """Calculate simplified Allan deviation for gyroscope stability"""
        # Simplified Allan variance calculation
        if len(data) < 100:
            return np.array([0.0, 0.0, 0.0])
        
        # Calculate first differences
        diffs = np.diff(data, axis=0)
        allan_var = 0.5 * np.mean(diffs**2, axis=0)
        allan_dev = np.sqrt(allan_var)
        
        return allan_dev
    
    def save_calibration(self, filename="icm20948_calibration.json"):
        """Save calibration data to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            print(f"✅ Calibration saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save calibration: {e}")
    
    def generate_calibration_report(self):
        """Generate comprehensive calibration report"""
        print("\n" + "=" * 60)
        print("📋 COMPLETE CALIBRATION REPORT")
        print("=" * 60)
        
        # Overall assessment
        total_abnormalities = len(self.calibration_data['abnormalities'])
        
        if total_abnormalities == 0:
            print("🎉 EXCELLENT! All sensors calibrated successfully")
            print("✅ No abnormalities detected")
            print("✅ Ready for high-precision EKF implementation")
        elif total_abnormalities <= 3:
            print("⚠️  GOOD calibration with minor issues")
            print(f"   {total_abnormalities} abnormalities detected")
            print("✅ Suitable for EKF implementation with awareness of issues")
        else:
            print("❌ POOR calibration - multiple issues detected")
            print(f"   {total_abnormalities} abnormalities detected")
            print("⚠️  Consider recalibration or hardware check")
        
        print(f"\nCalibration timestamp: {self.calibration_data['timestamp']}")
        
        # Detailed abnormalities
        if self.calibration_data['abnormalities']:
            print("\n🔍 DETECTED ABNORMALITIES:")
            for i, abnormality in enumerate(self.calibration_data['abnormalities'], 1):
                print(f"  {i}. {abnormality}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if total_abnormalities == 0:
            print("  • Proceed with EKF implementation")
            print("  • Consider periodic recalibration")
        else:
            print("  • Review abnormalities and consider fixes")
            print("  • Test in different environments")
            print("  • Consider temperature compensation")
        
        print("\n📁 Calibration data saved for EKF use")
    
    def close(self):
        """Close sensor connection"""
        if self.imu:
            self.imu.close()

def main():
    """Main calibration function"""
    print("🎯 ICM20948 Complete Sensor Calibration Suite")
    print("=" * 60)
    print("This will calibrate all sensors and detect abnormalities")
    print("⏱️  Total time required: ~20-30 minutes")
    print("📋 You will need to position the sensor in various orientations")
    print()
    
    input("Press Enter to start calibration...")
    
    calibrator = ICM20948_Calibration()
    
    try:
        # Initialize sensor
        if not calibrator.initialize_sensor():
            return
        
        # Run calibration sequence
        calibrator.calibrate_accelerometer()
        calibrator.calibrate_gyroscope()
        calibrator.calibrate_magnetometer()
        
        # Generate report and save
        calibrator.generate_calibration_report()
        calibrator.save_calibration()
        
        print("\n🎯 CALIBRATION COMPLETE!")
        print("Use the generated calibration file with your EKF implementation")
        
    except KeyboardInterrupt:
        print("\n\nCalibration interrupted by user")
        
    except Exception as e:
        print(f"\nCalibration error: {e}")
        
    finally:
        calibrator.close()

if __name__ == "__main__":
    main() 