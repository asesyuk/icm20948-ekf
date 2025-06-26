#!/usr/bin/env python3
"""
Simple ICM20948 Test - Configured for Address 0x69
Your ICM20948 is working at address 0x69!
"""

import time
import sys

try:
    import smbus
except ImportError:
    print("ERROR: smbus not found. Install with: sudo apt-get install python3-smbus")
    sys.exit(1)

# Your ICM20948 configuration
ICM20948_ADDRESS = 0x69  # Your ICM20948 is at this address
I2C_BUS = 1

# Registers
WHO_AM_I_REG = 0x00
REG_BANK_SEL = 0x7F

def test_icm20948():
    print("ICM20948 Quick Test (Address 0x69)")
    print("=" * 40)
    
    try:
        bus = smbus.SMBus(I2C_BUS)
        
        # Set bank 0 to access WHO_AM_I
        bus.write_byte_data(ICM20948_ADDRESS, REG_BANK_SEL, 0x00)
        time.sleep(0.01)
        
        # Read WHO_AM_I
        who_am_i = bus.read_byte_data(ICM20948_ADDRESS, WHO_AM_I_REG)
        
        print(f"ICM20948 at address 0x{ICM20948_ADDRESS:02X}")
        print(f"WHO_AM_I register: 0x{who_am_i:02X}")
        
        if who_am_i == 0xEA:
            print("✅ SUCCESS: ICM20948 is connected and working!")
            print("✅ Your wiring is correct!")
            print("✅ Ready for sensor data reading!")
            return True
        else:
            print(f"❌ Unexpected WHO_AM_I value (expected 0xEA, got 0x{who_am_i:02X})")
            return False
            
    except Exception as e:
        print(f"❌ Error communicating with ICM20948: {e}")
        return False

def read_sensor_sample():
    """Read a quick sample of sensor data"""
    print("\nReading sensor data sample...")
    
    try:
        bus = smbus.SMBus(I2C_BUS)
        
        # Set bank 0 for accelerometer data
        bus.write_byte_data(ICM20948_ADDRESS, REG_BANK_SEL, 0x00)
        time.sleep(0.01)
        
        # Read accelerometer data (registers 0x2D-0x32)
        accel_data = []
        for reg in range(0x2D, 0x33):
            accel_data.append(bus.read_byte_data(ICM20948_ADDRESS, reg))
        
        # Convert to 16-bit signed values
        accel_x = (accel_data[0] << 8) | accel_data[1]
        accel_y = (accel_data[2] << 8) | accel_data[3]
        accel_z = (accel_data[4] << 8) | accel_data[5]
        
        # Convert to signed
        if accel_x > 32767: accel_x -= 65536
        if accel_y > 32767: accel_y -= 65536
        if accel_z > 32767: accel_z -= 65536
        
        print(f"Accelerometer raw values:")
        print(f"  X: {accel_x:6d}")
        print(f"  Y: {accel_y:6d}")
        print(f"  Z: {accel_z:6d}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading sensor data: {e}")
        return False

if __name__ == "__main__":
    print("Testing your ICM20948 at address 0x69...\n")
    
    # Basic connection test
    if test_icm20948():
        # Try reading some sensor data
        read_sensor_sample()
        
        print("\n" + "=" * 40)
        print("🎉 CONGRATULATIONS!")
        print("Your ICM20948 is properly connected and working!")
        print("\nNext steps:")
        print("- Implement full sensor reading (accel, gyro, magnetometer)")
        print("- Add calibration routines")
        print("- Implement Extended Kalman Filter")
    else:
        print("\n" + "=" * 40)
        print("❌ Connection test failed")
        print("Run the full diagnostic: python3 troubleshoot_icm20948.py") 