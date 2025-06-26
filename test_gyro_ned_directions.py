#!/usr/bin/env python3
"""
ICM20948 Gyroscope NED Direction Test
Verify that gyroscope rotations are correctly mapped to NED coordinates
"""

import time
import sys
import math

try:
    from icm20948_ned_corrected import ICM20948_NED_Corrected
except ImportError:
    print("ERROR: Could not import the corrected sensor class")
    print("Make sure icm20948_ned_corrected.py is in the same directory")
    sys.exit(1)

def main():
    """Test gyroscope directions in NED coordinates"""
    print("🧭 ICM20948 Gyroscope NED Direction Test")
    print("="*50)
    print("Testing that rotations are correctly mapped to NED coordinates")
    print()
    print("In NED coordinates:")
    print("  X-axis (North): Roll rotations (around forward-back axis)")
    print("  Y-axis (East):  Pitch rotations (around left-right axis)")  
    print("  Z-axis (Down):  Yaw rotations (around up-down axis)")
    print()
    
    try:
        # Initialize corrected sensor
        imu = ICM20948_NED_Corrected()
        print()
        
        print("🔄 Gyroscope Direction Tests:")
        print("-" * 40)
        print("Keep sensor steady between tests to see baseline near 0°/s")
        print()
        
        # Test 1: Roll (X-axis rotation)
        input("Test 1 - ROLL: Push RIGHT wing DOWN and LEFT wing DOWN (like airplane banking)")
        input("Press Enter to start 5-second test...")
        print("Monitoring gyro_X (roll rate):")
        print("Expected: Positive when RIGHT wing DOWN, negative when LEFT wing DOWN")
        
        for i in range(50):
            gyro = imu.read_gyroscope_ned()
            print(f"Roll(X): {gyro[0]:+6.1f}°/s  Pitch(Y): {gyro[1]:+6.1f}°/s  Yaw(Z): {gyro[2]:+6.1f}°/s", end="\r")
            time.sleep(0.1)
        print("\n")
        
        # Test 2: Pitch (Y-axis rotation)  
        input("Test 2 - PITCH: Lift NOSE UP and push NOSE DOWN (like airplane pitch)")
        input("Press Enter to start 5-second test...")
        print("Monitoring gyro_Y (pitch rate):")
        print("Expected: Positive when NOSE UP, negative when NOSE DOWN")
        
        for i in range(50):
            gyro = imu.read_gyroscope_ned()
            print(f"Roll(X): {gyro[0]:+6.1f}°/s  Pitch(Y): {gyro[1]:+6.1f}°/s  Yaw(Z): {gyro[2]:+6.1f}°/s", end="\r")
            time.sleep(0.1)
        print("\n")
        
        # Test 3: Yaw (Z-axis rotation)
        input("Test 3 - YAW: Rotate sensor clockwise and counter-clockwise (like turning a steering wheel)")
        input("Press Enter to start 5-second test...")
        print("Monitoring gyro_Z (yaw rate):")
        print("Expected: Positive when rotating CLOCKWISE, negative when rotating COUNTER-CLOCKWISE")
        
        for i in range(50):
            gyro = imu.read_gyroscope_ned()
            print(f"Roll(X): {gyro[0]:+6.1f}°/s  Pitch(Y): {gyro[1]:+6.1f}°/s  Yaw(Z): {gyro[2]:+6.1f}°/s", end="\r")
            time.sleep(0.1)
        print("\n")
        
        # Continuous monitoring mode
        print("="*50)
        print("🔄 CONTINUOUS MONITORING MODE")
        print("Move the sensor and watch all three gyroscope axes:")
        print("Press Ctrl+C to stop")
        print()
        print("      Roll(X)    Pitch(Y)    Yaw(Z)    | Movement Guide")
        print("      °/s        °/s         °/s       |")
        print("-" * 55)
        
        while True:
            gyro = imu.read_gyroscope_ned()
            
            # Determine primary movement
            abs_x, abs_y, abs_z = abs(gyro[0]), abs(gyro[1]), abs(gyro[2])
            max_val = max(abs_x, abs_y, abs_z)
            
            movement = "Steady"
            if max_val > 10:  # Threshold for detecting movement
                if abs_x == max_val:
                    movement = "ROLL " + ("RIGHT-DOWN" if gyro[0] > 0 else "LEFT-DOWN")
                elif abs_y == max_val:
                    movement = "PITCH " + ("NOSE-UP" if gyro[1] > 0 else "NOSE-DOWN") 
                elif abs_z == max_val:
                    movement = "YAW " + ("CLOCKWISE" if gyro[2] > 0 else "COUNTER-CW")
            
            print(f"      {gyro[0]:+6.1f}     {gyro[1]:+6.1f}      {gyro[2]:+6.1f}     | {movement}", end="\r")
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🎯 Gyroscope NED Direction Test Complete!")
        print()
        print("✅ Verify these behaviors now match your movements:")
        print("   Roll (X):  RIGHT wing down = positive, LEFT wing down = negative")
        print("   Pitch (Y): NOSE UP = positive, NOSE DOWN = negative")
        print("   Yaw (Z):   CLOCKWISE rotation = positive, COUNTER-CLOCKWISE = negative")
        print()
        print("If the directions match, your gyroscope is correctly mapped to NED! 🚀")
        
    except Exception as e:
        print(f"\nError during test: {e}")
        
    finally:
        try:
            imu.close()
        except:
            pass

if __name__ == "__main__":
    main() 