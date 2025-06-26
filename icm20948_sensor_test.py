#!/usr/bin/env python3
"""
ICM20948 Sensor Data Reader and Orientation Test
Reads accelerometer, gyroscope, and magnetometer data
Helps verify sensor orientation and functionality
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

# Register Banks
REG_BANK_SEL = 0x7F

# Bank 0 Registers
WHO_AM_I = 0x00
PWR_MGMT_1 = 0x06
PWR_MGMT_2 = 0x07
ACCEL_XOUT_H = 0x2D
ACCEL_XOUT_L = 0x2E
ACCEL_YOUT_H = 0x2F
ACCEL_YOUT_L = 0x30
ACCEL_ZOUT_H = 0x31
ACCEL_ZOUT_L = 0x32
GYRO_XOUT_H = 0x33
GYRO_XOUT_L = 0x34
GYRO_YOUT_H = 0x35
GYRO_YOUT_L = 0x36
GYRO_ZOUT_H = 0x37
GYRO_ZOUT_L = 0x38

# Bank 2 Registers
ACCEL_CONFIG = 0x14
GYRO_CONFIG_1 = 0x01

# Magnetometer (AK09916) - accessed through auxiliary I2C
MAG_I2C_ADDR = 0x0C
MAG_WIA2 = 0x01  # Should read 0x09
MAG_ST1 = 0x10   # Status 1
MAG_HXL = 0x11   # X-axis data low byte
MAG_HXH = 0x12   # X-axis data high byte
MAG_HYL = 0x13   # Y-axis data low byte
MAG_HYH = 0x14   # Y-axis data high byte
MAG_HZL = 0x15   # Z-axis data low byte
MAG_HZH = 0x16   # Z-axis data high byte
MAG_ST2 = 0x18   # Status 2
MAG_CNTL2 = 0x31 # Control 2
MAG_CNTL3 = 0x32 # Control 3

class ICM20948:
    def __init__(self):
        self.bus = smbus.SMBus(I2C_BUS)
        self.initialize()
    
    def write_register(self, bank, register, value):
        """Write to a register in a specific bank"""
        # Set bank
        self.bus.write_byte_data(ICM20948_ADDRESS, REG_BANK_SEL, bank << 4)
        time.sleep(0.001)
        # Write register
        self.bus.write_byte_data(ICM20948_ADDRESS, register, value)
        time.sleep(0.001)
    
    def read_register(self, bank, register):
        """Read from a register in a specific bank"""
        # Set bank
        self.bus.write_byte_data(ICM20948_ADDRESS, REG_BANK_SEL, bank << 4)
        time.sleep(0.001)
        # Read register
        return self.bus.read_byte_data(ICM20948_ADDRESS, register)
    
    def read_registers(self, bank, start_register, length):
        """Read multiple registers in sequence"""
        # Set bank
        self.bus.write_byte_data(ICM20948_ADDRESS, REG_BANK_SEL, bank << 4)
        time.sleep(0.001)
        # Read registers
        return self.bus.read_i2c_block_data(ICM20948_ADDRESS, start_register, length)
    
    def initialize(self):
        """Initialize the ICM20948 sensor"""
        print("Initializing ICM20948...")
        
        # Reset device
        self.write_register(0, PWR_MGMT_1, 0x80)
        time.sleep(0.1)
        
        # Wake up device and set clock source
        self.write_register(0, PWR_MGMT_1, 0x01)
        time.sleep(0.01)
        
        # Enable accelerometer and gyroscope
        self.write_register(0, PWR_MGMT_2, 0x00)
        time.sleep(0.01)
        
        # Configure accelerometer (2g scale, 1125 Hz bandwidth)
        self.write_register(2, ACCEL_CONFIG, 0x00)
        time.sleep(0.01)
        
        # Configure gyroscope (250 dps scale, 1125 Hz bandwidth)
        self.write_register(2, GYRO_CONFIG_1, 0x00)
        time.sleep(0.01)
        
        print("✓ ICM20948 initialized successfully")
    
    def read_accel_raw(self):
        """Read raw accelerometer data"""
        data = self.read_registers(0, ACCEL_XOUT_H, 6)
        
        # Combine high and low bytes
        x = (data[0] << 8) | data[1]
        y = (data[2] << 8) | data[3]
        z = (data[4] << 8) | data[5]
        
        # Convert to signed 16-bit values
        if x > 32767: x -= 65536
        if y > 32767: y -= 65536
        if z > 32767: z -= 65536
        
        return x, y, z
    
    def read_gyro_raw(self):
        """Read raw gyroscope data"""
        data = self.read_registers(0, GYRO_XOUT_H, 6)
        
        # Combine high and low bytes
        x = (data[0] << 8) | data[1]
        y = (data[2] << 8) | data[3]
        z = (data[4] << 8) | data[5]
        
        # Convert to signed 16-bit values
        if x > 32767: x -= 65536
        if y > 32767: y -= 65536
        if z > 32767: z -= 65536
        
        return x, y, z
    
    def read_mag_raw(self):
        """Read raw magnetometer data (simplified - may need I2C master setup)"""
        try:
            # This is a simplified magnetometer read
            # Full implementation requires setting up I2C master mode
            # For now, return zeros and indicate not implemented
            return 0, 0, 0, False
        except Exception as e:
            return 0, 0, 0, False
    
    def convert_accel(self, raw_x, raw_y, raw_z):
        """Convert raw accelerometer data to g's (2g scale)"""
        scale = 2.0 / 32768.0  # 2g scale
        return raw_x * scale, raw_y * scale, raw_z * scale
    
    def convert_gyro(self, raw_x, raw_y, raw_z):
        """Convert raw gyroscope data to degrees per second (250 dps scale)"""
        scale = 250.0 / 32768.0  # 250 dps scale
        return raw_x * scale, raw_y * scale, raw_z * scale

def print_header():
    """Print data header"""
    print("\n" + "="*80)
    print("ICM20948 Sensor Data - Real Time")
    print("="*80)
    print("Press Ctrl+C to stop")
    print()
    print("Accelerometer (g)        Gyroscope (°/s)         Temperature")
    print("X      Y      Z          X      Y      Z")
    print("-"*80)

def print_orientation_guide():
    """Print orientation testing guide"""
    print("\n" + "="*60)
    print("SENSOR ORIENTATION TEST GUIDE")
    print("="*60)
    print("To verify correct sensor orientation, try these positions:")
    print()
    print("1. FLAT (chip facing up):")
    print("   Expected: X≈0, Y≈0, Z≈+1g (gravity pulling down)")
    print()
    print("2. UPSIDE DOWN (chip facing down):")
    print("   Expected: X≈0, Y≈0, Z≈-1g")
    print()
    print("3. ON SIDE (rotate around different axes):")
    print("   - Left side down: X≈+1g, Y≈0, Z≈0")
    print("   - Right side down: X≈-1g, Y≈0, Z≈0")
    print("   - Front edge down: X≈0, Y≈+1g, Z≈0")
    print("   - Back edge down: X≈0, Y≈-1g, Z≈0")
    print()
    print("4. ROTATION TEST (gyroscope):")
    print("   - Rotate around X-axis: X shows rotation")
    print("   - Rotate around Y-axis: Y shows rotation") 
    print("   - Rotate around Z-axis: Z shows rotation")
    print()
    print("Starting sensor reading in 3 seconds...")
    print("="*60)

def main():
    try:
        # Initialize sensor
        imu = ICM20948()
        
        # Show orientation guide
        print_orientation_guide()
        time.sleep(3)
        
        # Print header
        print_header()
        
        while True:
            # Read raw data
            accel_raw = imu.read_accel_raw()
            gyro_raw = imu.read_gyro_raw()
            mag_raw, mag_ok = imu.read_mag_raw()[:2], imu.read_mag_raw()[3]
            
            # Convert to physical units
            accel_g = imu.convert_accel(*accel_raw)
            gyro_dps = imu.convert_gyro(*gyro_raw)
            
            # Calculate magnitude for reference
            accel_magnitude = math.sqrt(sum(x*x for x in accel_g))
            
            # Print data in a clean format
            print(f"{accel_g[0]:+6.2f} {accel_g[1]:+6.2f} {accel_g[2]:+6.2f}    "
                  f"{gyro_dps[0]:+7.1f} {gyro_dps[1]:+7.1f} {gyro_dps[2]:+7.1f}    "
                  f"Mag: {accel_magnitude:.2f}g", end="\r")
            
            time.sleep(0.1)  # 10 Hz update rate
            
    except KeyboardInterrupt:
        print("\n\nStopping sensor reading...")
        print("\nSensor Test Summary:")
        print("- If accelerometer shows ~1g when stationary, it's working correctly")
        print("- If gyroscope shows ~0°/s when stationary, it's working correctly")
        print("- If values change when you move the sensor, orientation is correct")
        print("\nNext steps: Implement magnetometer and sensor fusion!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the sensor is connected and try again.")

if __name__ == "__main__":
    main() 