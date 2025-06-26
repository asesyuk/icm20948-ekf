#!/usr/bin/env python3
"""
ICM20948 Physical Orientation Guidance
Helps determine correct NED transformation based on physical mounting
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
ICM20948_ADDRESS = 0x69
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

def read_accelerometer(bus):
    """Read accelerometer data"""
    bus.write_byte_data(ICM20948_ADDRESS, 0x7F, 0x00)
    time.sleep(0.001)
    
    accel_data = bus.read_i2c_block_data(ICM20948_ADDRESS, 0x2D, 6)
    
    def to_signed16(high, low):
        value = (high << 8) | low
        return value - 65536 if value > 32767 else value
    
    accel_x = to_signed16(accel_data[0], accel_data[1])
    accel_y = to_signed16(accel_data[2], accel_data[3])
    accel_z = to_signed16(accel_data[4], accel_data[5])
    
    # Convert to g's
    accel_scale = 2.0 / 32768.0
    return (accel_x * accel_scale, accel_y * accel_scale, accel_z * accel_scale)

def determine_vehicle_orientation():
    """Interactive session to determine vehicle coordinate system"""
    
    print("ICM20948 Physical Orientation Guidance")
    print("=" * 60)
    print("Based on your photo, the ICM20948 is mounted with text readable.")
    print("This means:")
    print("  +X_sensor: Points RIGHT (east side of the board)")
    print("  +Y_sensor: Points UP in photo (north side of the board)")
    print("  +Z_sensor: Points UP (away from chip surface)")
    print()
    
    print("We need to determine how your sensor is oriented relative to")
    print("your vehicle/platform coordinate system.")
    print()
    
    # Get vehicle forward direction
    print("STEP 1: Determine FORWARD direction")
    print("-" * 40)
    print("Which direction does your vehicle/platform move FORWARD?")
    print("(Look at your mounted sensor board)")
    print()
    print("1. Toward the TOP of the board (where +Y_sensor points)")
    print("2. Toward the RIGHT of the board (where +X_sensor points)")  
    print("3. Toward the BOTTOM of the board (where -Y_sensor points)")
    print("4. Toward the LEFT of the board (where -X_sensor points)")
    print()
    
    while True:
        try:
            choice = int(input("Enter choice (1-4): "))
            if choice in [1, 2, 3, 4]:
                break
            else:
                print("Please enter 1, 2, 3, or 4")
        except ValueError:
            print("Please enter a number")
    
    forward_directions = {
        1: ("+Y_sensor", "Y", 1),
        2: ("+X_sensor", "X", 1), 
        3: ("-Y_sensor", "Y", -1),
        4: ("-X_sensor", "X", -1)
    }
    
    forward_desc, forward_axis, forward_sign = forward_directions[choice]
    
    print(f"\n✓ FORWARD direction: {forward_desc}")
    
    # Determine right direction
    print("\nSTEP 2: Determine RIGHT direction")
    print("-" * 40)
    print("Which direction is to the RIGHT of your vehicle/platform?")
    print("(When facing forward)")
    print()
    
    remaining_choices = []
    remaining_map = {}
    choice_num = 1
    
    directions = [
        ("+Y_sensor", "Y", 1),
        ("+X_sensor", "X", 1),
        ("-Y_sensor", "Y", -1), 
        ("-X_sensor", "X", -1)
    ]
    
    for desc, axis, sign in directions:
        if (axis, sign) != (forward_axis, forward_sign):
            print(f"{choice_num}. Toward the {desc.replace('_sensor', '').replace('+', '').replace('-', 'opposite of ')} of the board")
            remaining_map[choice_num] = (desc, axis, sign)
            choice_num += 1
    
    while True:
        try:
            choice = int(input(f"Enter choice (1-{choice_num-1}): "))
            if choice in remaining_map:
                break
            else:
                print(f"Please enter a number between 1 and {choice_num-1}")
        except ValueError:
            print("Please enter a number")
    
    right_desc, right_axis, right_sign = remaining_map[choice]
    
    print(f"\n✓ RIGHT direction: {right_desc}")
    
    # Calculate NED transformation
    print("\nSTEP 3: Calculate NED Transformation")
    print("-" * 40)
    
    # NED coordinate system requirements:
    # North (forward) = +X_ned
    # East (right) = +Y_ned  
    # Down = +Z_ned
    
    # Calculate transformations
    if forward_axis == "X":
        x_ned_transform = f"{'+' if forward_sign > 0 else '-'}X_sensor"
    else:  # forward_axis == "Y"
        x_ned_transform = f"{'+' if forward_sign > 0 else '-'}Y_sensor"
    
    if right_axis == "X":
        y_ned_transform = f"{'+' if right_sign > 0 else '-'}X_sensor"
    else:  # right_axis == "Y"
        y_ned_transform = f"{'+' if right_sign > 0 else '-'}Y_sensor"
    
    # Z is always -Z_sensor for NED (since chip Z points up, NED needs down positive)
    z_ned_transform = "-Z_sensor"
    
    print("\nRequired NED Transformation:")
    print("```python")
    print("def transform_to_ned(x_sensor, y_sensor, z_sensor):")
    print(f"    x_ned = {x_ned_transform}  # North")
    print(f"    y_ned = {y_ned_transform}  # East") 
    print(f"    z_ned = {z_ned_transform}  # Down")
    print("    return x_ned, y_ned, z_ned")
    print("```")
    
    return x_ned_transform, y_ned_transform, z_ned_transform

def test_transformation_live():
    """Test the transformation with live sensor data"""
    
    print("\nSTEP 4: Test Transformation (Optional)")
    print("-" * 40)
    test = input("Would you like to test the transformation with live data? (y/n): ").lower()
    
    if test != 'y':
        return
    
    try:
        bus = setup_icm20948()
        print("\n✓ ICM20948 initialized")
        print("\nLive sensor test - Press Ctrl+C to stop")
        print("Try tilting your platform and verify the directions make sense:")
        print("- Tilt FORWARD: X_ned should be positive")
        print("- Tilt RIGHT: Y_ned should be positive")  
        print("- Flat: Z_ned should be positive (~1g)")
        print()
        
        # Get transformation from previous step (simplified for demo)
        print("Sensor readings:")
        print("X_sens  Y_sens  Z_sens  |  N_ned  E_ned  D_ned  | Vehicle Orientation")
        print("-" * 70)
        
        while True:
            x_sensor, y_sensor, z_sensor = read_accelerometer(bus)
            
            # Apply the determined transformation (simplified example)
            # In real implementation, use the actual transformation determined above
            x_ned = x_sensor  # This would be replaced with actual transformation
            y_ned = y_sensor  # This would be replaced with actual transformation  
            z_ned = -z_sensor  # This is correct for NED
            
            # Determine approximate orientation
            if abs(z_ned) > 0.7:
                orientation = "LEVEL" if z_ned > 0 else "UPSIDE DOWN"
            elif abs(y_ned) > 0.7:
                orientation = "TILTED FORWARD" if y_ned > 0 else "TILTED BACKWARD"
            elif abs(x_ned) > 0.7:
                orientation = "TILTED RIGHT" if x_ned > 0 else "TILTED LEFT"
            else:
                orientation = "TILTED"
            
            print(f"{x_sensor:+6.2f}  {y_sensor:+6.2f}  {z_sensor:+6.2f}  |  "
                  f"{x_ned:+6.2f}  {y_ned:+6.2f}  {z_ned:+6.2f}  | {orientation}", end="\r")
            
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\n\nTest completed!")
    except Exception as e:
        print(f"\nError: {e}")

def main():
    print("This script will help you determine the correct NED transformation")
    print("for your ICM20948 based on its physical mounting orientation.")
    print()
    
    try:
        # Determine orientation
        x_transform, y_transform, z_transform = determine_vehicle_orientation()
        
        print(f"\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("Your NED transformation:")
        print(f"  X_ned = {x_transform}  # North (forward)")
        print(f"  Y_ned = {y_transform}  # East (right)")
        print(f"  Z_ned = {z_transform}  # Down")
        print()
        print("Implementation:")
        print("1. Update your sensor class with this transformation")
        print("2. Test with live data to verify correctness")
        print("3. Proceed with EKF implementation")
        
        # Optional live test
        test_transformation_live()
        
    except KeyboardInterrupt:
        print("\nGuidance session cancelled.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main() 