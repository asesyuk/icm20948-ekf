#!/usr/bin/env python3
"""
ICM20948 Magnetometer NED Direction Test
Verify that magnetometer readings are correctly mapped to NED coordinates
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

def calculate_heading(mag_x, mag_y):
    """Calculate heading from magnetometer readings (NED coordinates)"""
    # In NED: X=North, Y=East
    # Heading = atan2(East, North) converted to degrees (0-360°)
    heading_rad = math.atan2(mag_y, mag_x)
    heading_deg = math.degrees(heading_rad)
    
    # Convert to 0-360° range
    if heading_deg < 0:
        heading_deg += 360
        
    return heading_deg

def heading_to_direction(heading):
    """Convert heading to cardinal direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(heading / 22.5) % 16
    return directions[index]

def main():
    """Test magnetometer directions in NED coordinates"""
    print("🧭 ICM20948 Magnetometer NED Direction Test")
    print("="*60)
    print("Testing that magnetic field is correctly mapped to NED coordinates")
    print()
    print("In NED coordinates:")
    print("  X-axis (North): Magnetic North component")
    print("  Y-axis (East):  Magnetic East component")  
    print("  Z-axis (Down):  Magnetic Down component (inclination)")
    print()
    print("Expected behavior:")
    print("  Point NORTH: X_mag = positive maximum, Y_mag ≈ 0")
    print("  Point EAST:  X_mag ≈ 0, Y_mag = positive maximum")
    print("  Point SOUTH: X_mag = negative maximum, Y_mag ≈ 0")
    print("  Point WEST:  X_mag ≈ 0, Y_mag = negative maximum")
    print()
    
    try:
        # Initialize sensor
        imu = ICM20948_NED_Corrected()
        print()
        
        # Check if magnetometer is working
        mag_x, mag_y, mag_z, valid = imu.read_magnetometer_ned()
        if not valid:
            print("❌ Magnetometer not working properly!")
            print("   Check magnetometer initialization and connections.")
            return
        
        print("✅ Magnetometer initialized and working")
        print()
        
        print("🧪 MAGNETOMETER DIRECTION TESTS:")
        print("-" * 45)
        print("Rotate the sensor to point in different directions.")
        print("Watch how the magnetic field components change.")
        print()
        
        # Test 1: Direction test
        print("Test 1 - CARDINAL DIRECTIONS:")
        print("Slowly rotate your sensor to point North, East, South, West")
        print("Watch the X_mag and Y_mag values and calculated heading")
        input("Press Enter to start continuous monitoring...")
        print()
        print("   X_mag    Y_mag    Z_mag   |  Heading  | Direction | Strength")
        print("   (µT)     (µT)     (µT)    |   (°)     |           |   (µT)")
        print("-" * 70)
        
        try:
            for i in range(100):  # Run for 10 seconds
                mag_x, mag_y, mag_z, valid = imu.read_magnetometer_ned()
                
                if valid:
                    # Calculate heading and magnetic field strength
                    heading = calculate_heading(mag_x, mag_y)
                    direction = heading_to_direction(heading)
                    strength = math.sqrt(mag_x**2 + mag_y**2 + mag_z**2)
                    
                    print(f"  {mag_x:+7.1f}  {mag_y:+7.1f}  {mag_z:+7.1f}  | {heading:5.1f}°   | {direction:>3}       | {strength:6.1f}")
                else:
                    print("  Invalid magnetometer reading")
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            pass
        
        print("\n")
        
        # Test 2: Calibration check
        print("Test 2 - MAGNETOMETER CALIBRATION CHECK:")
        print("Slowly rotate the sensor in a full 360° horizontal circle")
        print("This will show if the magnetometer needs calibration")
        input("Press Enter to start 15-second calibration check...")
        print()
        
        readings = []
        print("Collecting readings... (rotate sensor in a full circle)")
        
        for i in range(150):  # 15 seconds of readings
            mag_x, mag_y, mag_z, valid = imu.read_magnetometer_ned()
            if valid:
                readings.append((mag_x, mag_y, mag_z))
                heading = calculate_heading(mag_x, mag_y)
                print(f"Reading {i+1:3d}: X={mag_x:+6.1f} Y={mag_y:+6.1f} Z={mag_z:+6.1f} Heading={heading:5.1f}°", end="\r")
            time.sleep(0.1)
        
        print("\n")
        
        # Analyze calibration
        if readings:
            x_vals = [r[0] for r in readings]
            y_vals = [r[1] for r in readings]
            z_vals = [r[2] for r in readings]
            
            x_min, x_max = min(x_vals), max(x_vals)
            y_min, y_max = min(y_vals), max(y_vals)
            z_min, z_max = min(z_vals), max(z_vals)
            
            x_center = (x_max + x_min) / 2
            y_center = (y_max + y_min) / 2
            z_center = (z_max + z_min) / 2
            
            x_range = x_max - x_min
            y_range = y_max - y_min
            z_range = z_max - z_min
            
            print("📊 CALIBRATION ANALYSIS:")
            print("-" * 25)
            print(f"X-axis: min={x_min:+6.1f} max={x_max:+6.1f} center={x_center:+6.1f} range={x_range:6.1f}")
            print(f"Y-axis: min={y_min:+6.1f} max={y_max:+6.1f} center={y_center:+6.1f} range={y_range:6.1f}")
            print(f"Z-axis: min={z_min:+6.1f} max={z_max:+6.1f} center={z_center:+6.1f} range={z_range:6.1f}")
            print()
            
            # Check if calibration is needed
            center_threshold = 20  # µT
            range_threshold = 50   # µT
            
            needs_cal = (abs(x_center) > center_threshold or 
                        abs(y_center) > center_threshold or
                        x_range < range_threshold or 
                        y_range < range_threshold)
            
            if needs_cal:
                print("⚠️  CALIBRATION RECOMMENDED:")
                print("   • Centers should be near 0")
                print("   • Ranges should be similar and > 50µT")
                print("   • Consider implementing hard/soft iron calibration")
            else:
                print("✅ CALIBRATION LOOKS GOOD:")
                print("   • Centers are close to zero")
                print("   • Ranges indicate good magnetic field variation")
        
        print()
        
        # Test 3: Continuous monitoring
        print("Test 3 - CONTINUOUS MONITORING:")
        print("Move and rotate the sensor to verify magnetometer behavior")
        print("Press Ctrl+C to stop")
        print()
        print("    Mag_X     Mag_Y     Mag_Z   |  Heading  | Direction | Notes")
        print("    (µT)      (µT)      (µT)    |    (°)    |           |")
        print("-" * 75)
        
        while True:
            mag_x, mag_y, mag_z, valid = imu.read_magnetometer_ned()
            
            if valid:
                heading = calculate_heading(mag_x, mag_y)
                direction = heading_to_direction(heading)
                strength = math.sqrt(mag_x**2 + mag_y**2 + mag_z**2)
                
                # Determine dominant axis
                abs_x, abs_y = abs(mag_x), abs(mag_y)
                if abs_x > abs_y * 1.5:
                    note = "Pointing N/S"
                elif abs_y > abs_x * 1.5:
                    note = "Pointing E/W"
                else:
                    note = "Diagonal"
                
                print(f"  {mag_x:+8.1f}  {mag_y:+8.1f}  {mag_z:+8.1f}  | {heading:6.1f}°  | {direction:>3}       | {note}", end="\r")
            else:
                print("  Invalid magnetometer reading", end="\r")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🎯 Magnetometer NED Direction Test Complete!")
        print()
        print("✅ Verify these behaviors matched your movements:")
        print("   • Point NORTH: X_mag positive maximum, Y_mag ≈ 0")
        print("   • Point EAST:  Y_mag positive maximum, X_mag ≈ 0")
        print("   • Point SOUTH: X_mag negative maximum, Y_mag ≈ 0")
        print("   • Point WEST:  Y_mag negative maximum, X_mag ≈ 0")
        print()
        print("📋 For EKF Implementation:")
        print("   • Use heading = atan2(Y_mag, X_mag) for yaw correction")
        print("   • Consider implementing magnetometer calibration")
        print("   • Z_mag provides magnetic inclination information")
        print()
        print("If directions match, your magnetometer is correctly mapped to NED! 🚀")
        
    except Exception as e:
        print(f"\nError during test: {e}")
        
    finally:
        try:
            imu.close()
        except:
            pass

if __name__ == "__main__":
    main() 