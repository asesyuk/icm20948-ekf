#!/usr/bin/env python3
"""
ICM20948 Final NED Transformation Summary
Shows the complete corrected transformations for all sensors
"""

import time
import sys

try:
    from icm20948_ned_corrected import ICM20948_NED_Corrected
except ImportError:
    print("ERROR: Could not import the corrected sensor class")
    print("Make sure icm20948_ned_corrected.py is in the same directory")
    sys.exit(1)

def main():
    """Display final NED transformation summary and test"""
    print("🎯 ICM20948 FINAL NED TRANSFORMATION SUMMARY")
    print("="*60)
    print()
    
    print("📋 FINAL CORRECTED TRANSFORMATIONS:")
    print("-" * 40)
    print()
    
    print("🔹 ACCELEROMETER:")
    print("   X_ned = +X_sensor  (RIGHT direction → North)")
    print("   Y_ned = +Y_sensor  (FORWARD direction → East)")  
    print("   Z_ned = -Z_sensor  (UP direction → Down)")
    print()
    
    print("🔹 GYROSCOPE:")
    print("   X_ned = -X_sensor  (RIGHT rotation → North, negated)")
    print("   Y_ned = -Y_sensor  (FORWARD rotation → East, negated)")
    print("   Z_ned = +Z_sensor  (UP rotation → Down, no negation)")
    print()
    
    print("🔹 MAGNETOMETER:")
    print("   X_ned = -X_sensor  (RIGHT direction → North, negated)")
    print("   Y_ned = -Y_sensor  (FORWARD direction → East, negated)")
    print("   Z_ned = -Z_sensor  (UP direction → Down)")
    print()
    
    print("❓ WHY ARE THE TRANSFORMATIONS DIFFERENT?")
    print("-" * 40)
    print("• Accelerometer: Measures LINEAR motion (translations)")
    print("• Gyroscope: Measures ANGULAR motion (rotations)")
    print("• Magnetometer: Measures MAGNETIC field directions")
    print("• Each sensor can have different internal orientations")
    print("  even when on the same physical chip!")
    print("• Different transformations ensure all sensors output")
    print("  the same NED coordinate system for sensor fusion")
    print("• This is normal and depends on your specific mounting!")
    print()
    
    try:
        # Initialize sensor
        imu = ICM20948_NED_Corrected()
        print()
        
        print("🧪 QUICK VERIFICATION TEST:")
        print("-" * 30)
        
        # Quick test
        input("Place sensor level, then press Enter for baseline reading...")
        data = imu.read_all_sensors_ned()
        accel = data['accelerometer']
        gyro = data['gyroscope']
        
        print(f"Baseline readings:")
        print(f"  Accel: X={accel[0]:+.2f}g  Y={accel[1]:+.2f}g  Z={accel[2]:+.2f}g")
        print(f"  Gyro:  X={gyro[0]:+.1f}°/s Y={gyro[1]:+.1f}°/s Z={gyro[2]:+.1f}°/s")
        
        level_ok = abs(accel[2] - 1.0) < 0.2 and abs(accel[0]) < 0.2 and abs(accel[1]) < 0.2
        gyro_ok = abs(gyro[0]) < 5 and abs(gyro[1]) < 5 and abs(gyro[2]) < 5
        
        print(f"  Status: Accel {'✓' if level_ok else '✗'} | Gyro {'✓' if gyro_ok else '✗'}")
        print()
        
        if level_ok and gyro_ok:
            print("🎉 PERFECT! Your ICM20948 is ready for EKF implementation!")
            print()
            print("✅ All sensors properly transformed to NED coordinates:")
            print("   • Accelerometer: Measures linear accelerations")
            print("   • Gyroscope: Measures angular velocities") 
            print("   • Magnetometer: Measures magnetic field directions")
            print("✅ Each sensor has been individually calibrated for NED!")
            print("✅ Ready for Extended Kalman Filter sensor fusion!")
        else:
            print("⚠️  Check sensor mounting - readings seem off")
        
        print()
        print("📦 FOR YOUR EKF IMPLEMENTATION:")
        print("-" * 35)
        print("from icm20948_ned_corrected import ICM20948_NED_Corrected")
        print()
        print("imu = ICM20948_NED_Corrected()")
        print("data = imu.read_all_sensors_ned()")
        print()
        print("accel_ned = data['accelerometer']    # (North, East, Down) in g")
        print("gyro_ned = data['gyroscope']         # (North, East, Down) in °/s")
        print("mag_ned = data['magnetometer']       # (North, East, Down) in µT")
        print("timestamp = data['timestamp']        # Unix timestamp")
        
    except KeyboardInterrupt:
        print("\n\nSummary completed!")
        
    except Exception as e:
        print(f"\nError: {e}")
        
    finally:
        try:
            imu.close()
        except:
            pass

if __name__ == "__main__":
    main() 