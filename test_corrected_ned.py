#!/usr/bin/env python3
"""
Quick Test for Corrected NED Transformation
Based on your test results showing 90-degree sensor rotation
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
    """Quick verification test for the corrected NED transformation"""
    print("🔧 CORRECTED NED Transformation Test")
    print("="*50)
    print("Based on your sensor showing 90-degree rotation")
    print("New transformation:")
    print("  X_ned = +X_sensor  (RIGHT → North)")
    print("  Y_ned = +Y_sensor  (FORWARD → East)")
    print("  Z_ned = -Z_sensor  (UP → Down)")
    print()
    
    try:
        # Initialize corrected sensor
        imu = ICM20948_NED_Corrected()
        print()
        
        # Interactive test
        print("🧪 Quick Verification Tests:")
        print("-" * 30)
        
        # Test 1: Level
        input("1. Place sensor LEVEL on table, then press Enter...")
        accel = imu.read_accelerometer_ned()
        print(f"   Result: X_ned={accel[0]:+.2f}g  Y_ned={accel[1]:+.2f}g  Z_ned={accel[2]:+.2f}g")
        level_ok = abs(accel[2] - 1.0) < 0.2 and abs(accel[0]) < 0.2 and abs(accel[1]) < 0.2
        print(f"   Status: {'✓ PASS' if level_ok else '✗ FAIL'} (Z should be ~+1g)")
        print()
        
        # Test 2: Forward tilt
        input("2. Tilt sensor FORWARD (vehicle forward direction), then press Enter...")
        accel = imu.read_accelerometer_ned()
        print(f"   Result: X_ned={accel[0]:+.2f}g  Y_ned={accel[1]:+.2f}g  Z_ned={accel[2]:+.2f}g")
        forward_ok = accel[0] > 0.5
        print(f"   Status: {'✓ PASS' if forward_ok else '✗ FAIL'} (X_ned should be positive)")
        print()
        
        # Test 3: Right tilt  
        input("3. Tilt sensor RIGHT (vehicle right direction), then press Enter...")
        accel = imu.read_accelerometer_ned()
        print(f"   Result: X_ned={accel[0]:+.2f}g  Y_ned={accel[1]:+.2f}g  Z_ned={accel[2]:+.2f}g")
        right_ok = accel[1] > 0.5
        print(f"   Status: {'✓ PASS' if right_ok else '✗ FAIL'} (Y_ned should be positive)")
        print()
        
        # Summary
        tests_passed = sum([level_ok, forward_ok, right_ok])
        print("="*50)
        print(f"CORRECTED TRANSFORMATION TEST RESULTS: {tests_passed}/3 PASSED")
        
        if tests_passed == 3:
            print("🎉 SUCCESS! Corrected NED transformation is working!")
            print("✅ Your ICM20948 is now properly oriented for EKF")
            print("✅ Use 'icm20948_ned_corrected.py' for your EKF implementation")
        else:
            print("⚠️  Some tests failed - may need further adjustment")
            print("   Check your sensor mounting and transformation matrix")
        
        print("\n📋 Final NED Transformation Summary:")
        print("   X_ned = +X_sensor  (Your RIGHT → North)")
        print("   Y_ned = +Y_sensor  (Your FORWARD → East)")  
        print("   Z_ned = -Z_sensor  (UP → Down)")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        
    except Exception as e:
        print(f"\nError during test: {e}")
        
    finally:
        try:
            imu.close()
        except:
            pass

if __name__ == "__main__":
    main() 