#!/usr/bin/env python3
"""
Quick ICM20948 Orientation Test
Simple script to verify accelerometer and gyroscope orientation
"""

import time
import sys
import math

try:
    import smbus
except ImportError:
    print("ERROR: smbus not found. Install with: sudo apt-get install python3-smbus")
    sys.exit(1)

# ICM20948 Configuration
ICM20948_ADDRESS = 0x69  # Your device address
I2C_BUS = 1

def setup_icm20948():
    """Basic ICM20948 setup"""
    bus = smbus.SMBus(I2C_BUS)
    
    # Set bank 0
    bus.write_byte_data(ICM20948_ADDRESS, 0x7F, 0x00)
    time.sleep(0.01)
    
    # Wake up device
    bus.write_byte_data(ICM20948_ADDRESS, 0x06, 0x01)
    time.sleep(0.01)
    
    # Enable accel and gyro
    bus.write_byte_data(ICM20948_ADDRESS, 0x07, 0x00)
    time.sleep(0.01)
    
    return bus

def read_sensors(bus):
    """Read accelerometer and gyroscope data"""
    # Set bank 0
    bus.write_byte_data(ICM20948_ADDRESS, 0x7F, 0x00)
    time.sleep(0.001)
    
    # Read accel data (6 bytes starting at 0x2D)
    accel_data = bus.read_i2c_block_data(ICM20948_ADDRESS, 0x2D, 6)
    
    # Read gyro data (6 bytes starting at 0x33)
    gyro_data = bus.read_i2c_block_data(ICM20948_ADDRESS, 0x33, 6)
    
    # Convert to signed 16-bit values
    def to_signed16(high, low):
        value = (high << 8) | low
        return value - 65536 if value > 32767 else value
    
    accel_x = to_signed16(accel_data[0], accel_data[1])
    accel_y = to_signed16(accel_data[2], accel_data[3])
    accel_z = to_signed16(accel_data[4], accel_data[5])
    
    gyro_x = to_signed16(gyro_data[0], gyro_data[1])
    gyro_y = to_signed16(gyro_data[2], gyro_data[3])
    gyro_z = to_signed16(gyro_data[4], gyro_data[5])
    
    # Convert to physical units
    accel_scale = 2.0 / 32768.0  # ±2g range
    gyro_scale = 250.0 / 32768.0  # ±250°/s range
    
    accel_g = (accel_x * accel_scale, accel_y * accel_scale, accel_z * accel_scale)
    gyro_dps = (gyro_x * gyro_scale, gyro_y * gyro_scale, gyro_z * gyro_scale)
    
    return accel_g, gyro_dps

def print_orientation_status(accel_g):
    """Determine and print current orientation (NED coordinate system)"""
    x, y, z = accel_g
    
    # Find the dominant axis
    abs_x, abs_y, abs_z = abs(x), abs(y), abs(z)
    
    if abs_z > 0.7:  # Z-axis dominant - determines Z direction
        if z > 0:
            orientation = "FLAT - Z+ pointing UP (away from earth)"
        else:
            orientation = "FLAT - Z- pointing DOWN (toward earth) [NED compliant]"
    elif abs_x > 0.7:  # X-axis dominant (points LEFT on chip)
        if x > 0:
            orientation = "TILTED LEFT - X+ pointing DOWN"
        else:
            orientation = "TILTED RIGHT - X- pointing DOWN"
    elif abs_y > 0.7:  # Y-axis dominant (points FORWARD on chip)
        if y > 0:
            orientation = "TILTED FORWARD - Y+ pointing DOWN"
        else:
            orientation = "TILTED BACKWARD - Y- pointing DOWN"
    else:
        orientation = "TILTED/MOVING"
    
    return orientation

def main():
    print("ICM20948 Quick Orientation Test")
    print("=" * 50)
    print("This will show real-time sensor data to verify orientation")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Setup sensor
        bus = setup_icm20948()
        print("✓ ICM20948 initialized")
        
        print("\nTEST INSTRUCTIONS (NED Coordinate System):")
        print("Your sensor orientation:")
        print("  X axis: Points LEFT")
        print("  Y axis: Points FORWARD")
        print("  Z axis: Direction to be determined from gravity")
        print()
        print("1. Place FLAT - should show ~1g on Z axis")
        print("2. Tilt LEFT (X down) - should show ~1g on X axis")
        print("3. Tilt FORWARD (Y down) - should show ~1g on Y axis")
        print("4. Rotate sensor - gyroscope values should change")
        print("\nStarting test...\n")
        
        while True:
            # Read sensor data
            accel_g, gyro_dps = read_sensors(bus)
            
            # Calculate total acceleration magnitude
            accel_magnitude = math.sqrt(sum(x*x for x in accel_g))
            
            # Get orientation
            orientation = print_orientation_status(accel_g)
            
            # Print results
            print(f"Accel: X:{accel_g[0]:+6.2f}g Y:{accel_g[1]:+6.2f}g Z:{accel_g[2]:+6.2f}g "
                  f"|{accel_magnitude:.2f}g| - {orientation}")
            print(f"Gyro:  X:{gyro_dps[0]:+6.1f}°/s Y:{gyro_dps[1]:+6.1f}°/s Z:{gyro_dps[2]:+6.1f}°/s", end="\r")
            
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\n\nTest completed!")
        print("\nVERIFICATION CHECKLIST (NED Coordinate System):")
        print("✓ Accelerometer magnitude should be ~1.0g when stationary")
        print("✓ Gyroscope should read ~0°/s when not rotating")
        print("✓ Z-axis should show which way is UP/DOWN (determines Z direction)")
        print("✓ X-axis should respond when tilting LEFT")
        print("✓ Y-axis should respond when tilting FORWARD")
        print("✓ Gyroscope values should spike when you rotate the sensor")
        print("\nNED COMPLIANCE CHECK:")
        print("  - If Z is negative when flat → Z points DOWN (NED compliant)")
        print("  - If Z is positive when flat → Z points UP (need to invert for NED)")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure ICM20948 is connected at address 0x69")

if __name__ == "__main__":
    main() 