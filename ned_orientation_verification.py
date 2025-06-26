#!/usr/bin/env python3
"""
ICM20948 NED Orientation Verification Test
Verifies correct NED convention: X=North, Y=East, Z=Down
Interactive test to confirm sensor orientation is working correctly
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

def read_sensors_ned(bus):
    """Read sensors and apply NED transformation"""
    bus.write_byte_data(ICM20948_ADDRESS, 0x7F, 0x00)
    time.sleep(0.001)
    
    # Read accelerometer data
    accel_data = bus.read_i2c_block_data(ICM20948_ADDRESS, 0x2D, 6)
    
    # Read gyroscope data
    gyro_data = bus.read_i2c_block_data(ICM20948_ADDRESS, 0x33, 6)
    
    def to_signed16(high, low):
        value = (high << 8) | low
        return value - 65536 if value > 32767 else value
    
    # Convert accelerometer raw values
    accel_x_raw = to_signed16(accel_data[0], accel_data[1])
    accel_y_raw = to_signed16(accel_data[2], accel_data[3])
    accel_z_raw = to_signed16(accel_data[4], accel_data[5])
    
    # Convert gyroscope raw values
    gyro_x_raw = to_signed16(gyro_data[0], gyro_data[1])
    gyro_y_raw = to_signed16(gyro_data[2], gyro_data[3])
    gyro_z_raw = to_signed16(gyro_data[4], gyro_data[5])
    
    # Convert to physical units
    accel_scale = 2.0 / 32768.0  # ±2g scale
    gyro_scale = 250.0 / 32768.0  # ±250°/s scale
    
    accel_x_sensor = accel_x_raw * accel_scale
    accel_y_sensor = accel_y_raw * accel_scale
    accel_z_sensor = accel_z_raw * accel_scale
    
    gyro_x_sensor = gyro_x_raw * gyro_scale
    gyro_y_sensor = gyro_y_raw * gyro_scale
    gyro_z_sensor = gyro_z_raw * gyro_scale
    
    # Apply NED transformation: X=North, Y=East, Z=Down
    accel_x_ned = +accel_y_sensor  # FORWARD → North (X-axis in NED)
    accel_y_ned = +accel_x_sensor  # RIGHT → East (Y-axis in NED)
    accel_z_ned = -accel_z_sensor  # UP → Down (Z-axis in NED, negated)
    
    gyro_x_ned = +gyro_y_sensor    # FORWARD rotation → North (X-axis in NED)
    gyro_y_ned = +gyro_x_sensor    # RIGHT rotation → East (Y-axis in NED)
    gyro_z_ned = -gyro_z_sensor    # UP rotation → Down (Z-axis in NED, negated)
    
    return {
        'accel_sensor': (accel_x_sensor, accel_y_sensor, accel_z_sensor),
        'accel_ned': (accel_x_ned, accel_y_ned, accel_z_ned),
        'gyro_sensor': (gyro_x_sensor, gyro_y_sensor, gyro_z_sensor),
        'gyro_ned': (gyro_x_ned, gyro_y_ned, gyro_z_ned)
    }

def determine_orientation_ned(accel_ned):
    """Determine orientation based on NED accelerometer readings"""
    x_north, y_east, z_down = accel_ned
    
    # Find dominant axis
    abs_north = abs(x_north)
    abs_east = abs(y_east)
    abs_down = abs(z_down)
    
    if abs_down > 0.7:  # Z (Down) dominant
        if z_down > 0:
            return "LEVEL (Down is positive - correct NED)"
        else:
            return "UPSIDE DOWN (Down is negative)"
    elif abs_north > 0.7:  # X (North) dominant
        if x_north > 0:
            return "TILTED FORWARD (North positive)"
        else:
            return "TILTED BACKWARD (North negative)"
    elif abs_east > 0.7:  # Y (East) dominant
        if y_east > 0:
            return "TILTED RIGHT (East positive)"
        else:
            return "TILTED LEFT (East negative)"
    else:
        return "TILTED (multiple axes)"

def print_ned_explanation():
    """Print explanation of NED coordinate system"""
    print("NED (North-East-Down) Coordinate System Verification")
    print("=" * 60)
    print("Standard Navigation Convention:")
    print("  X-axis = NORTH (Forward direction)")
    print("  Y-axis = EAST (Right direction)")  
    print("  Z-axis = DOWN (Toward Earth)")
    print()
    print("Your ICM20948 sensor transformation:")
    print("  X_ned = +Y_sensor  (Forward → North)")
    print("  Y_ned = +X_sensor  (Right → East)")
    print("  Z_ned = -Z_sensor  (Up → Down, negated)")
    print()

def interactive_orientation_test():
    """Interactive test to verify NED orientation"""
    print("Interactive NED Orientation Test")
    print("-" * 40)
    print("This test will guide you through verifying correct NED orientation.")
    print("Follow the instructions and confirm the readings match expectations.")
    print()
    
    try:
        bus = setup_icm20948()
        print("✓ ICM20948 initialized")
        print()
        
        tests = [
            {
                'name': "Level Test",
                'instruction': "Place the sensor FLAT and LEVEL on a table",
                'expected': "Z_ned (Down) should be ~+1.0g, X_ned and Y_ned should be ~0g",
                'check': lambda data: abs(data['accel_ned'][2] - 1.0) < 0.3 and abs(data['accel_ned'][0]) < 0.3 and abs(data['accel_ned'][1]) < 0.3
            },
            {
                'name': "Forward Tilt Test", 
                'instruction': "Tilt the sensor FORWARD (in the direction your vehicle would move forward)",
                'expected': "X_ned (North) should be positive, Y_ned and Z_ned should be smaller",
                'check': lambda data: data['accel_ned'][0] > 0.5
            },
            {
                'name': "Backward Tilt Test",
                'instruction': "Tilt the sensor BACKWARD (opposite of forward direction)",
                'expected': "X_ned (North) should be negative, Y_ned and Z_ned should be smaller", 
                'check': lambda data: data['accel_ned'][0] < -0.5
            },
            {
                'name': "Right Tilt Test",
                'instruction': "Tilt the sensor to the RIGHT (in the direction that would be right/starboard)",
                'expected': "Y_ned (East) should be positive, X_ned and Z_ned should be smaller",
                'check': lambda data: data['accel_ned'][1] > 0.5
            },
            {
                'name': "Left Tilt Test", 
                'instruction': "Tilt the sensor to the LEFT (opposite of right direction)",
                'expected': "Y_ned (East) should be negative, X_ned and Z_ned should be smaller",
                'check': lambda data: data['accel_ned'][1] < -0.5
            }
        ]
        
        results = []
        
        for i, test in enumerate(tests, 1):
            print(f"Test {i}/5: {test['name']}")
            print(f"Instruction: {test['instruction']}")
            print(f"Expected: {test['expected']}")
            input("Press Enter when ready...")
            
            # Take measurement
            time.sleep(0.5)  # Allow sensor to stabilize
            data = read_sensors_ned(bus)
            accel_ned = data['accel_ned']
            orientation = determine_orientation_ned(accel_ned)
            
            # Display results
            print(f"Results: X_ned={accel_ned[0]:+6.2f}g  Y_ned={accel_ned[1]:+6.2f}g  Z_ned={accel_ned[2]:+6.2f}g")
            print(f"Orientation: {orientation}")
            
            # Check if test passed
            passed = test['check'](data)
            result_str = "✓ PASS" if passed else "✗ FAIL"
            print(f"Test Result: {result_str}")
            
            results.append((test['name'], passed, accel_ned))
            print("-" * 60)
            print()
        
        # Summary
        print("NED ORIENTATION TEST SUMMARY")
        print("=" * 60)
        passed_count = sum(1 for _, passed, _ in results if passed)
        
        for name, passed, readings in results:
            status = "✓ PASS" if passed else "✗ FAIL" 
            print(f"{name:<20} {status}  (X:{readings[0]:+5.2f}, Y:{readings[1]:+5.2f}, Z:{readings[2]:+5.2f})")
        
        print(f"\nOverall Result: {passed_count}/5 tests passed")
        
        if passed_count >= 4:
            print("🎉 EXCELLENT! Your NED orientation is correctly configured!")
            print("✓ Ready for Extended Kalman Filter implementation")
        elif passed_count >= 3:
            print("⚠️  MOSTLY CORRECT - Minor adjustments may be needed")
            print("Check the failed tests and verify your coordinate system")
        else:
            print("❌ ORIENTATION ISSUES DETECTED")
            print("Please check your sensor mounting and transformation matrix")
        
        return passed_count >= 4
        
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        return False
    except Exception as e:
        print(f"Error during test: {e}")
        return False

def continuous_monitoring_mode():
    """Continuous monitoring mode with live NED data"""
    print("\nContinuous NED Monitoring Mode")
    print("-" * 40)
    print("Real-time display of NED coordinates")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        bus = setup_icm20948()
        
        print("Accelerometer (g)     Gyroscope (°/s)      Orientation")
        print("N      E      D       N      E      D")
        print("-" * 60)
        
        while True:
            data = read_sensors_ned(bus)
            accel_ned = data['accel_ned']
            gyro_ned = data['gyro_ned']
            orientation = determine_orientation_ned(accel_ned)
            
            # Calculate magnitude for reference
            magnitude = math.sqrt(sum(x*x for x in accel_ned))
            
            print(f"{accel_ned[0]:+6.2f} {accel_ned[1]:+6.2f} {accel_ned[2]:+6.2f}   "
                  f"{gyro_ned[0]:+6.1f} {gyro_ned[1]:+6.1f} {gyro_ned[2]:+6.1f}   "
                  f"{orientation:<25} |{magnitude:.2f}g|", end="\r")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")
    except Exception as e:
        print(f"\nError: {e}")

def main():
    """Main function"""
    print_ned_explanation()
    
    print("Choose test mode:")
    print("1. Interactive Orientation Test (Recommended)")
    print("2. Continuous Monitoring Mode")
    print("3. Both (Interactive test followed by monitoring)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice in ['1', '3']:
            success = interactive_orientation_test()
            
            if choice == '3':
                if success:
                    print("\nOrientation test passed! Starting continuous monitoring...")
                    time.sleep(2)
                    continuous_monitoring_mode()
                else:
                    cont = input("\nOrientation test had issues. Continue to monitoring? (y/n): ")
                    if cont.lower() == 'y':
                        continuous_monitoring_mode()
        
        elif choice == '2':
            continuous_monitoring_mode()
        
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nProgram terminated")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 