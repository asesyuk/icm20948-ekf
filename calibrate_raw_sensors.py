#!/usr/bin/env python3
"""
ICM20948 RAW Sensor Calibration Suite - CORRECTED VERSION
Calibrates raw sensor data BEFORE applying NED transformations
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

class ICM20948_RawCalibration:
    """Raw sensor calibration suite for ICM20948 (before NED transformation)"""
    
    def __init__(self):
        self.imu = None
        self.calibration_data = {
            'timestamp': datetime.now().isoformat(),
            'coordinate_system': 'raw_sensor_coordinates',
            'accelerometer': {},
            'gyroscope': {},
            'magnetometer': {},
            'abnormalities': [],
            'notes': 'Calibration performed on RAW sensor data before NED transformation'
        }
        
    def initialize_sensor(self):
        """Initialize the sensor"""
        print("🔧 Initializing ICM20948...")
        try:
            self.imu = ICM20948_NED_Corrected()
            print("✅ Sensor initialized successfully")
            print("📋 NOTE: Calibrating RAW sensor coordinates (before NED transformation)")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize sensor: {e}")
            return False
    
    def read_raw_accelerometer(self):
        """Read raw accelerometer data in physical units"""
        accel_raw = self.imu.read_accelerometer_raw()
        return [x * self.imu.accel_scale for x in accel_raw]
    
    def read_raw_gyroscope(self):
        """Read raw gyroscope data in physical units"""
        gyro_raw = self.imu.read_gyroscope_raw()
        return [x * self.imu.gyro_scale for x in gyro_raw]
    
    def read_raw_magnetometer(self):
        """Read raw magnetometer data in physical units"""
        mag_raw_x, mag_raw_y, mag_raw_z, mag_valid = self.imu.read_magnetometer_raw()
        if mag_valid:
            return [mag_raw_x * self.imu.mag_scale, 
                   mag_raw_y * self.imu.mag_scale, 
                   mag_raw_z * self.imu.mag_scale], True
        return [0, 0, 0], False
    
    def collect_raw_static_data(self, duration=10, description=""):
        """Collect RAW sensor data while stationary"""
        print(f"📊 Collecting RAW {description} data for {duration} seconds...")
        print("⚠️  Keep sensor completely still!")
        
        accel_data = []
        gyro_data = []
        mag_data = []
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # Read RAW sensor data (before NED transformation)
            accel_g = self.read_raw_accelerometer()
            gyro_dps = self.read_raw_gyroscope()
            mag_ut, mag_valid = self.read_raw_magnetometer()
            
            accel_data.append(accel_g)
            gyro_data.append(gyro_dps)
            if mag_valid:
                mag_data.append(mag_ut)
            
            # Progress indicator
            elapsed = time.time() - start_time
            progress = int((elapsed / duration) * 20)
            bar = "█" * progress + "░" * (20 - progress)
            print(f"\r[{bar}] {elapsed:.1f}s", end="")
            
            time.sleep(0.05)  # 20Hz sampling
        
        print("\n✅ RAW data collection complete")
        return np.array(accel_data), np.array(gyro_data), np.array(mag_data)
    
    def calibrate_raw_accelerometer(self):
        """Calibrate RAW accelerometer bias and scale factors"""
        print("\n🎯 RAW ACCELEROMETER CALIBRATION")
        print("=" * 50)
        print("📋 Using RAW sensor coordinates (before NED transformation)")
        print("   X_raw = sensor's physical X-axis")
        print("   Y_raw = sensor's physical Y-axis")  
        print("   Z_raw = sensor's physical Z-axis")
        print()
        
        # Step 1: Collect static data (level)
        input("Place sensor LEVEL on a stable surface. Press Enter...")
        accel_level, _, _ = self.collect_raw_static_data(10, "level accelerometer")
        
        # Step 2: Collect data in 6 orientations for scale factor calibration
        orientations = [
            ("RAW Sensor X+ pointing UP", [1, 0, 0]),
            ("RAW Sensor X- pointing UP", [-1, 0, 0]),
            ("RAW Sensor Y+ pointing UP", [0, 1, 0]),
            ("RAW Sensor Y- pointing UP", [0, -1, 0]),
            ("RAW Sensor Z+ pointing UP", [0, 0, 1]),
            ("RAW Sensor Z- pointing UP", [0, 0, -1])
        ]
        
        orientation_data = []
        for desc, expected in orientations:
            input(f"Orient sensor: {desc}. Press Enter...")
            accel_data, _, _ = self.collect_raw_static_data(5, f"accelerometer {desc}")
            orientation_data.append((accel_data, expected))
        
        # Analyze RAW accelerometer data
        self.analyze_raw_accelerometer_data(accel_level, orientation_data)
    
    def analyze_raw_accelerometer_data(self, level_data, orientation_data):
        """Analyze RAW accelerometer calibration data"""
        print("\n📊 Analyzing RAW accelerometer data...")
        
        # Calculate bias (offset when level)
        bias_raw = np.mean(level_data, axis=0)
        
        # Determine which axis measures gravity when level
        gravity_axis = np.argmax(np.abs(bias_raw))
        gravity_direction = np.sign(bias_raw[gravity_axis])
        
        # Subtract gravity from the appropriate axis
        bias_corrected = bias_raw.copy()
        bias_corrected[gravity_axis] -= gravity_direction * 1.0  # Remove 1g
        
        # Calculate noise levels
        noise = np.std(level_data, axis=0)
        
        # Analyze scale factors from 6-point calibration
        scale_errors = []
        axis_scales = [1.0, 1.0, 1.0]
        
        for accel_data, expected in orientation_data:
            mean_reading = np.mean(accel_data, axis=0)
            
            # Find which physical axis should have +1g or -1g
            expected_axis = np.argmax(np.abs(expected))
            expected_value = expected[expected_axis]
            measured_value = mean_reading[expected_axis]
            
            if abs(expected_value) > 0.5:  # Valid orientation
                # Calculate scale factor for this axis
                actual_scale = abs(measured_value)
                scale_error = abs(actual_scale - 1.0)
                scale_errors.append(scale_error)
                axis_scales[expected_axis] = actual_scale
        
        # Store calibration results
        self.calibration_data['accelerometer'] = {
            'bias_raw': bias_corrected.tolist(),
            'noise_std': noise.tolist(),
            'scale_factors': axis_scales,
            'scale_errors': scale_errors,
            'max_scale_error': max(scale_errors) if scale_errors else 0.0,
            'gravity_axis': int(gravity_axis),
            'gravity_direction': float(gravity_direction)
        }
        
        # Check for abnormalities
        abnormalities = []
        if max(np.abs(bias_corrected)) > 0.2:
            abnormalities.append("Excessive accelerometer bias in RAW coordinates")
        if max(noise) > 0.05:
            abnormalities.append("Excessive accelerometer noise")
        if max(scale_errors) > 0.1:
            abnormalities.append("Accelerometer scale factor error")
        
        self.calibration_data['abnormalities'].extend(abnormalities)
        
        # Display results
        print(f"  RAW Bias (g):         X={bias_corrected[0]:+.3f}, Y={bias_corrected[1]:+.3f}, Z={bias_corrected[2]:+.3f}")
        print(f"  RAW Noise (g):        X={noise[0]:.3f}, Y={noise[1]:.3f}, Z={noise[2]:.3f}")
        print(f"  RAW Scale factors:    X={axis_scales[0]:.3f}, Y={axis_scales[1]:.3f}, Z={axis_scales[2]:.3f}")
        if scale_errors:
            print(f"  Max scale error:      {max(scale_errors):.1%}")
        print(f"  Gravity axis:         {['X', 'Y', 'Z'][gravity_axis]} ({'up' if gravity_direction > 0 else 'down'})")
        
        if abnormalities:
            print("  ⚠️  Abnormalities detected:")
            for abnormality in abnormalities:
                print(f"     • {abnormality}")
        else:
            print("  ✅ RAW accelerometer calibration looks good")
    
    def calibrate_raw_gyroscope(self):
        """Calibrate RAW gyroscope bias and analyze noise"""
        print("\n🎯 RAW GYROSCOPE CALIBRATION")
        print("=" * 50)
        print("📋 Using RAW sensor coordinates (before NED transformation)")
        
        # Step 1: Collect static data for bias calibration
        input("Keep sensor completely still for RAW gyroscope bias calibration. Press Enter...")
        _, gyro_static, _ = self.collect_raw_static_data(30, "gyroscope bias")
        
        # Analyze RAW gyroscope data
        self.analyze_raw_gyroscope_data(gyro_static)
    
    def analyze_raw_gyroscope_data(self, static_data):
        """Analyze RAW gyroscope calibration data"""
        print("\n📊 Analyzing RAW gyroscope data...")
        
        # Calculate bias (drift when stationary)
        bias = np.mean(static_data, axis=0)
        
        # Calculate noise and stability
        noise = np.std(static_data, axis=0)
        
        # Allan variance calculation (simplified)
        allan_dev = self.calculate_allan_deviation(static_data)
        
        # Store calibration results
        self.calibration_data['gyroscope'] = {
            'bias_raw': bias.tolist(),
            'noise_std': noise.tolist(),
            'allan_deviation': allan_dev.tolist()
        }
        
        # Check for abnormalities
        abnormalities = []
        if max(np.abs(bias)) > 2.0:  # Bias > 2°/s
            abnormalities.append("Excessive gyroscope bias in RAW coordinates")
        if max(noise) > 0.5:  # Noise > 0.5°/s
            abnormalities.append("Excessive gyroscope noise")
        if max(allan_dev) > 1.0:  # Allan deviation > 1°/s
            abnormalities.append("Poor gyroscope stability (Allan variance)")
        
        self.calibration_data['abnormalities'].extend(abnormalities)
        
        # Display results
        print(f"  RAW Bias (°/s):       X={bias[0]:+.2f}, Y={bias[1]:+.2f}, Z={bias[2]:+.2f}")
        print(f"  RAW Noise (°/s):      X={noise[0]:.2f}, Y={noise[1]:.2f}, Z={noise[2]:.2f}")
        print(f"  Allan deviation:      X={allan_dev[0]:.2f}, Y={allan_dev[1]:.2f}, Z={allan_dev[2]:.2f}")
        
        if abnormalities:
            print("  ⚠️  Abnormalities detected:")
            for abnormality in abnormalities:
                print(f"     • {abnormality}")
        else:
            print("  ✅ RAW gyroscope calibration looks good")
    
    def calibrate_raw_magnetometer(self):
        """Calibrate RAW magnetometer hard/soft iron effects"""
        print("\n🎯 RAW MAGNETOMETER CALIBRATION")
        print("=" * 50)
        print("📋 Using RAW sensor coordinates (before NED transformation)")
        
        print("Magnetometer calibration requires rotating the sensor in 3D space")
        print("to map the magnetic field sphere in RAW sensor coordinates.")
        print()
        
        input("Press Enter to start RAW magnetometer sphere mapping...")
        
        # Collect RAW magnetometer data while rotating in 3D
        print("🔄 Rotate sensor slowly in ALL directions for 60 seconds:")
        print("  • Roll it like a ball")
        print("  • Tumble it in 3D space")
        print("  • Cover as many orientations as possible")
        
        _, _, mag_data = self.collect_raw_static_data(60, "3D magnetometer rotation")
        
        if len(mag_data) < 100:
            print("❌ Insufficient RAW magnetometer data collected")
            return
        
        # Analyze RAW magnetometer data
        self.analyze_raw_magnetometer_data(mag_data)
    
    def analyze_raw_magnetometer_data(self, mag_data):
        """Analyze RAW magnetometer calibration data and fit sphere"""
        print("\n📊 Analyzing RAW magnetometer data...")
        
        if len(mag_data) == 0:
            print("❌ No valid RAW magnetometer data")
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
            'hard_iron_offset_raw': hard_iron_offset.tolist(),
            'soft_iron_scale_raw': soft_iron_scale.tolist(),
            'mean_field_strength': float(mean_strength),
            'field_strength_variation': float(strength_variation),
            'field_ranges_raw': field_ranges.tolist(),
            'data_points': len(mag_data)
        }
        
        # Check for abnormalities
        abnormalities = []
        if max(np.abs(hard_iron_offset)) > 100:
            abnormalities.append("Large hard iron offset in RAW coordinates")
        if strength_variation / mean_strength > 0.3:
            abnormalities.append("Large magnetic field variation (poor calibration)")
        if min(field_ranges) < 50:
            abnormalities.append("Insufficient magnetometer calibration coverage")
        if len(mag_data) < 500:
            abnormalities.append("Insufficient magnetometer calibration data")
        if mean_strength < 20 or mean_strength > 80:
            abnormalities.append("Unusual magnetic field strength")
        
        self.calibration_data['abnormalities'].extend(abnormalities)
        
        # Display results
        print(f"  RAW Hard iron (µT):   X={hard_iron_offset[0]:+.1f}, Y={hard_iron_offset[1]:+.1f}, Z={hard_iron_offset[2]:+.1f}")
        print(f"  RAW Soft iron scale:  X={soft_iron_scale[0]:.3f}, Y={soft_iron_scale[1]:.3f}, Z={soft_iron_scale[2]:.3f}")
        print(f"  Mean field strength:  {mean_strength:.1f} µT")
        print(f"  Field variation:      {strength_variation:.1f} µT ({strength_variation/mean_strength:.1%})")
        print(f"  Data points:          {len(mag_data)}")
        
        if abnormalities:
            print("  ⚠️  Abnormalities detected:")
            for abnormality in abnormalities:
                print(f"     • {abnormality}")
        else:
            print("  ✅ RAW magnetometer calibration looks good")
    
    def calculate_allan_deviation(self, data):
        """Calculate simplified Allan deviation for gyroscope stability"""
        if len(data) < 100:
            return np.array([0.0, 0.0, 0.0])
        
        diffs = np.diff(data, axis=0)
        allan_var = 0.5 * np.mean(diffs**2, axis=0)
        allan_dev = np.sqrt(allan_var)
        
        return allan_dev
    
    def save_calibration(self, filename="icm20948_raw_calibration.json"):
        """Save RAW calibration data to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            print(f"✅ RAW calibration saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save calibration: {e}")
    
    def generate_calibration_report(self):
        """Generate comprehensive RAW calibration report"""
        print("\n" + "=" * 60)
        print("📋 RAW SENSOR CALIBRATION REPORT")
        print("=" * 60)
        print("📋 NOTE: All calibration performed on RAW sensor coordinates")
        print("   (BEFORE applying NED coordinate transformations)")
        
        # Overall assessment
        total_abnormalities = len(self.calibration_data['abnormalities'])
        
        if total_abnormalities == 0:
            print("🎉 EXCELLENT! All RAW sensors calibrated successfully")
            print("✅ No abnormalities detected in RAW sensor data")
            print("✅ Ready for applying NED transformations and EKF implementation")
        elif total_abnormalities <= 3:
            print("⚠️  GOOD RAW calibration with minor issues")
            print(f"   {total_abnormalities} abnormalities detected")
            print("✅ Suitable for NED transformation and EKF implementation")
        else:
            print("❌ POOR RAW calibration - multiple issues detected")
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
        print("  • Apply these calibration parameters to RAW sensor data")
        print("  • THEN apply NED coordinate transformations")  
        print("  • Use corrected data for EKF implementation")
        if total_abnormalities > 0:
            print("  • Review abnormalities and consider environmental factors")
        
        print("\n📁 RAW calibration data saved for proper EKF integration")
    
    def close(self):
        """Close sensor connection"""
        if self.imu:
            self.imu.close()

def main():
    """Main RAW calibration function"""
    print("🎯 ICM20948 RAW Sensor Calibration Suite")
    print("=" * 60)
    print("📋 This calibrates sensors in their ORIGINAL coordinate system")
    print("   (BEFORE applying NED transformations)")
    print("⏱️  Total time required: ~20-30 minutes")
    print("📋 You will need to position the sensor in various orientations")
    print()
    
    input("Press Enter to start RAW calibration...")
    
    calibrator = ICM20948_RawCalibration()
    
    try:
        # Initialize sensor
        if not calibrator.initialize_sensor():
            return
        
        # Run RAW calibration sequence
        calibrator.calibrate_raw_accelerometer()
        calibrator.calibrate_raw_gyroscope()
        calibrator.calibrate_raw_magnetometer()
        
        # Generate report and save
        calibrator.generate_calibration_report()
        calibrator.save_calibration()
        
        print("\n🎯 RAW CALIBRATION COMPLETE!")
        print("Apply these parameters to RAW data, then use NED transformations")
        
    except KeyboardInterrupt:
        print("\n\nRAW calibration interrupted by user")
        
    except Exception as e:
        print(f"\nRAW calibration error: {e}")
        
    finally:
        calibrator.close()

if __name__ == "__main__":
    main() 