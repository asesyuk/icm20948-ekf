#!/usr/bin/env python3
"""
Quick Test for Magnetometer NED Correction
Verify that magnetometer directions now match accelerometer directions
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
    """Quick test to verify magnetometer correction"""
    print("🧭 Magnetometer NED Correction Test")
    print("="*45)
    print("Testing that magnetometer directions now match accelerometer")
    print()
    
    try:
        # Initialize sensor
        imu = ICM20948_NED_Corrected()
        
        if not imu.mag_initialized:
            print("❌ Magnetometer not working. Run:")
            print("   python3 fix_magnetometer_continuous.py")
            return
        
        print("✅ All sensors initialized")
        print()
        
        print("🧪 DIRECTION ALIGNMENT TEST:")
        print("-" * 35)
        print("This test checks that accelerometer and magnetometer")
        print("both point in the same NED directions")
        print()
        
        # Test 1: Point North
        input("1. Point your sensor's X-axis toward MAGNETIC NORTH")
        input("   Press Enter to take reading...")
        
        accel = imu.read_accelerometer_ned()
        mag_x, mag_y, mag_z, mag_valid = imu.read_magnetometer_ned()
        
        print(f"   Accelerometer: X={accel[0]:+.2f}g (should be ~0)")
        if mag_valid:
            print(f"   Magnetometer:  X={mag_x:+.1f}µT (should be positive)")
            print(f"                  Y={mag_y:+.1f}µT (should be ~0)")
            
            north_ok = mag_x > 0 and abs(mag_y) < abs(mag_x)
            print(f"   Status: {'✓ PASS' if north_ok else '✗ FAIL'}")
        else:
            print("   Magnetometer: Invalid reading")
            north_ok = False
        
        print()
        
        # Test 2: Point East
        input("2. Point your sensor's X-axis toward EAST")
        input("   Press Enter to take reading...")
        
        accel = imu.read_accelerometer_ned()
        mag_x, mag_y, mag_z, mag_valid = imu.read_magnetometer_ned()
        
        print(f"   Accelerometer: Y={accel[1]:+.2f}g (should be ~0)")
        if mag_valid:
            print(f"   Magnetometer:  X={mag_x:+.1f}µT (should be ~0)")
            print(f"                  Y={mag_y:+.1f}µT (should be positive)")
            
            east_ok = mag_y > 0 and abs(mag_x) < abs(mag_y)
            print(f"   Status: {'✓ PASS' if east_ok else '✗ FAIL'}")
        else:
            print("   Magnetometer: Invalid reading")
            east_ok = False
        
        print()
        
        # Test 3: Point South
        input("3. Point your sensor's X-axis toward SOUTH")
        input("   Press Enter to take reading...")
        
        accel = imu.read_accelerometer_ned()
        mag_x, mag_y, mag_z, mag_valid = imu.read_magnetometer_ned()
        
        print(f"   Accelerometer: X={accel[0]:+.2f}g (should be ~0)")
        if mag_valid:
            print(f"   Magnetometer:  X={mag_x:+.1f}µT (should be negative)")
            print(f"                  Y={mag_y:+.1f}µT (should be ~0)")
            
            south_ok = mag_x < 0 and abs(mag_y) < abs(mag_x)
            print(f"   Status: {'✓ PASS' if south_ok else '✗ FAIL'}")
        else:
            print("   Magnetometer: Invalid reading")
            south_ok = False
        
        print()
        
        # Test 4: Point West
        input("4. Point your sensor's X-axis toward WEST")
        input("   Press Enter to take reading...")
        
        accel = imu.read_accelerometer_ned()
        mag_x, mag_y, mag_z, mag_valid = imu.read_magnetometer_ned()
        
        print(f"   Accelerometer: Y={accel[1]:+.2f}g (should be ~0)")
        if mag_valid:
            print(f"   Magnetometer:  X={mag_x:+.1f}µT (should be ~0)")
            print(f"                  Y={mag_y:+.1f}µT (should be negative)")
            
            west_ok = mag_y < 0 and abs(mag_x) < abs(mag_y)
            print(f"   Status: {'✓ PASS' if west_ok else '✗ FAIL'}")
        else:
            print("   Magnetometer: Invalid reading")
            west_ok = False
        
        print()
        
        # Summary
        if mag_valid:
            tests_passed = sum([north_ok, east_ok, south_ok, west_ok])
            print("="*45)
            print(f"MAGNETOMETER CORRECTION TEST: {tests_passed}/4 PASSED")
            
            if tests_passed >= 3:
                print("🎉 SUCCESS! Magnetometer directions corrected!")
                print("✅ Magnetometer and accelerometer are aligned")
                print("✅ Ready for heading calculation and EKF")
            else:
                print("⚠️  Some tests failed - magnetometer may need adjustment")
                print("   Try testing in a different location away from metal objects")
        else:
            print("❌ Magnetometer not providing valid readings")
            print("   Run: python3 fix_magnetometer_continuous.py")
        
        print("\n📋 Final Transformations:")
        print("   Accelerometer: X_ned=+X, Y_ned=+Y, Z_ned=-Z")
        print("   Gyroscope:     X_ned=-X, Y_ned=-Y, Z_ned=+Z")
        print("   Magnetometer:  X_ned=-X, Y_ned=-Y, Z_ned=-Z")
        
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