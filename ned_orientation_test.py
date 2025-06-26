#!/usr/bin/env python3
"""
ICM20948 NED Orientation Determination Test
Compares actual sensor orientation with datasheet and determines NED transformations
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

def analyze_orientation(measurements):
    """Analyze orientation measurements to determine coordinate system"""
    print("\n" + "="*80)
    print("ORIENTATION ANALYSIS")
    print("="*80)
    
    print("Datasheet ICM20948 orientation:")
    print("  +X: Points RIGHT (East)")
    print("  +Y: Points FORWARD (North)")  
    print("  +Z: Points UP (away from chip)")
    print()
    
    print("Your measurements:")
    for desc, values in measurements:
        x, y, z = values
        print(f"  {desc}: X={x:+6.2f}g, Y={y:+6.2f}g, Z={z:+6.2f}g")
    
    print("\nAnalysis:")
    
    # Find which axis responds to gravity in each position
    flat_x, flat_y, flat_z = measurements[0][1]  # Flat position
    
    # Determine Z direction
    if abs(flat_z) > 0.7:
        if flat_z > 0:
            print("  ✓ Z-axis points UP (positive when flat)")
            z_direction = "UP"
        else:
            print("  ✓ Z-axis points DOWN (negative when flat)")
            z_direction = "DOWN"
    else:
        print("  ⚠ Z-axis unclear from flat measurement")
        z_direction = "UNKNOWN"
    
    # Check X and Y from tilt measurements
    if len(measurements) >= 3:
        left_x, left_y, left_z = measurements[1][1]  # Left tilt
        forward_x, forward_y, forward_z = measurements[2][1]  # Forward tilt
        
        print(f"  When tilted LEFT: X={left_x:+5.2f}g")
        print(f"  When tilted FORWARD: Y={forward_y:+5.2f}g")
        
        # Determine coordinate system relative to datasheet
        if left_x > 0.7:
            x_direction = "LEFT (matches your description, opposite of datasheet)"
        elif left_x < -0.7:
            x_direction = "RIGHT (matches datasheet)"
        else:
            x_direction = "UNCLEAR"
            
        if forward_y > 0.7:
            y_direction = "FORWARD (matches datasheet)"
        elif forward_y < -0.7:
            y_direction = "BACKWARD (opposite of datasheet)"
        else:
            y_direction = "UNCLEAR"
            
        print(f"  X-axis points: {x_direction}")
        print(f"  Y-axis points: {y_direction}")
    
    print(f"  Z-axis points: {z_direction}")
    
    # Calculate NED transformations
    print("\n" + "="*80)
    print("NED TRANSFORMATION REQUIRED")
    print("="*80)
    print("NED (North-East-Down) requires:")
    print("  North: FORWARD (+Y in NED)")
    print("  East:  RIGHT (+X in NED)") 
    print("  Down:  TOWARD EARTH (+Z in NED)")
    print()
    
    # Determine transformations needed
    transformations = []
    
    if len(measurements) >= 3:
        # X transformation
        if left_x > 0.7:  # X points LEFT when tilted left
            transformations.append("X_ned = -X_sensor  # (LEFT → West, need to negate for East)")
        elif left_x < -0.7:  # X points RIGHT when tilted left  
            transformations.append("X_ned = +X_sensor  # (RIGHT → East, no change needed)")
        
        # Y transformation
        if forward_y > 0.7:  # Y points FORWARD when tilted forward
            transformations.append("Y_ned = +Y_sensor  # (FORWARD → North, no change needed)")
        elif forward_y < -0.7:  # Y points BACKWARD when tilted forward
            transformations.append("Y_ned = -Y_sensor  # (BACKWARD, need to negate for North)")
    
    # Z transformation
    if flat_z > 0.7:  # Z points UP when flat
        transformations.append("Z_ned = -Z_sensor  # (UP → need to negate for Down)")
    elif flat_z < -0.7:  # Z points DOWN when flat
        transformations.append("Z_ned = +Z_sensor  # (DOWN → no change needed)")
    
    print("Required transformations for NED compliance:")
    for transform in transformations:
        print(f"  {transform}")
    
    if not transformations:
        print("  ⚠ Cannot determine transformations - need clearer measurements")
    
    return transformations

def main():
    print("ICM20948 NED Orientation Determination Test")
    print("="*60)
    print("This test will determine your sensor's exact orientation")
    print("compared to the datasheet and calculate NED transformations.")
    print()
    print("You said:")
    print("  - X points LEFT on your sensor")
    print("  - Y points FORWARD on your sensor")
    print("  - Z direction unknown")
    print()
    print("Datasheet says:")
    print("  - +X points RIGHT")
    print("  - +Y points FORWARD") 
    print("  - +Z points UP")
    print()
    
    try:
        bus = setup_icm20948()
        print("✓ ICM20948 initialized")
        
        measurements = []
        
        # Test 1: Flat
        input("\n1. Place sensor FLAT on table, press Enter...")
        time.sleep(0.5)
        flat_reading = read_accelerometer(bus)
        measurements.append(("FLAT", flat_reading))
        print(f"   Flat: X={flat_reading[0]:+6.2f}g, Y={flat_reading[1]:+6.2f}g, Z={flat_reading[2]:+6.2f}g")
        
        # Test 2: Tilt LEFT (what you call LEFT direction)
        input("\n2. Tilt sensor so the LEFT side goes down, press Enter...")
        time.sleep(0.5)
        left_reading = read_accelerometer(bus)
        measurements.append(("TILTED LEFT", left_reading))
        print(f"   Left: X={left_reading[0]:+6.2f}g, Y={left_reading[1]:+6.2f}g, Z={left_reading[2]:+6.2f}g")
        
        # Test 3: Tilt FORWARD (what you call FORWARD direction)
        input("\n3. Tilt sensor so the FORWARD side goes down, press Enter...")
        time.sleep(0.5)
        forward_reading = read_accelerometer(bus)
        measurements.append(("TILTED FORWARD", forward_reading))
        print(f"   Forward: X={forward_reading[0]:+6.2f}g, Y={forward_reading[1]:+6.2f}g, Z={forward_reading[2]:+6.2f}g")
        
        # Analyze results
        transformations = analyze_orientation(measurements)
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        if transformations:
            print("✓ Orientation determined successfully!")
            print("\nTo convert your sensor data to NED coordinates, use:")
            print("```python")
            for transform in transformations:
                print(transform)
            print("```")
        else:
            print("⚠ Could not determine clear orientation.")
            print("Try the test again with more pronounced tilts.")
        
        print(f"\nSensor is at I2C address: 0x{ICM20948_ADDRESS:02X}")
        print("Ready for NED-compliant sensor fusion implementation!")
        
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main() 