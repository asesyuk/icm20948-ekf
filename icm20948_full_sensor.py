#!/usr/bin/env python3
"""
Complete ICM20948 9-DOF Sensor Reader
Includes accelerometer, gyroscope, and magnetometer
With proper I2C master setup for AK09916 magnetometer
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
INT_PIN_CFG = 0x0F
I2C_MST_STATUS = 0x17
ACCEL_XOUT_H = 0x2D
GYRO_XOUT_H = 0x33
EXT_SLV_SENS_DATA_00 = 0x3B

# Bank 3 Registers (I2C Master)
I2C_MST_CTRL = 0x01
I2C_SLV0_ADDR = 0x03
I2C_SLV0_REG = 0x04
I2C_SLV0_CTRL = 0x05
I2C_SLV0_DO = 0x06

# Bank 2 Registers
ACCEL_CONFIG = 0x14
GYRO_CONFIG_1 = 0x01

# Magnetometer (AK09916) Constants
MAG_I2C_ADDR = 0x0C
MAG_WIA2 = 0x01  # Should read 0x09
MAG_ST1 = 0x10   # Status 1
MAG_HXL = 0x11   # X-axis data low
MAG_HXH = 0x12   # X-axis data high
MAG_HYL = 0x13   # Y-axis data low
MAG_HYH = 0x14   # Y-axis data high
MAG_HZL = 0x15   # Z-axis data low
MAG_HZH = 0x16   # Z-axis data high
MAG_ST2 = 0x18   # Status 2
MAG_CNTL2 = 0x31 # Control 2
MAG_CNTL3 = 0x32 # Control 3

class ICM20948:
    def __init__(self):
        self.bus = smbus.SMBus(I2C_BUS)
        self.mag_initialized = False
        self.initialize()
    
    def write_register(self, bank, register, value):
        """Write to a register in a specific bank"""
        self.bus.write_byte_data(ICM20948_ADDRESS, REG_BANK_SEL, bank << 4)
        time.sleep(0.001)
        self.bus.write_byte_data(ICM20948_ADDRESS, register, value)
        time.sleep(0.001)
    
    def read_register(self, bank, register):
        """Read from a register in a specific bank"""
        self.bus.write_byte_data(ICM20948_ADDRESS, REG_BANK_SEL, bank << 4)
        time.sleep(0.001)
        return self.bus.read_byte_data(ICM20948_ADDRESS, register)
    
    def read_registers(self, bank, start_register, length):
        """Read multiple registers in sequence"""
        self.bus.write_byte_data(ICM20948_ADDRESS, REG_BANK_SEL, bank << 4)
        time.sleep(0.001)
        return self.bus.read_i2c_block_data(ICM20948_ADDRESS, start_register, length)
    
    def write_mag_register(self, register, value):
        """Write to magnetometer register via I2C master"""
        self.write_register(3, I2C_SLV0_ADDR, MAG_I2C_ADDR)  # Set magnetometer address
        self.write_register(3, I2C_SLV0_REG, register)       # Set register
        self.write_register(3, I2C_SLV0_DO, value)           # Set value to write
        self.write_register(3, I2C_SLV0_CTRL, 0x81)          # Enable write (1 byte)
        time.sleep(0.01)
    
    def read_mag_registers(self, register, length):
        """Read from magnetometer registers via I2C master"""
        self.write_register(3, I2C_SLV0_ADDR, MAG_I2C_ADDR | 0x80)  # Set read mode
        self.write_register(3, I2C_SLV0_REG, register)              # Set start register
        self.write_register(3, I2C_SLV0_CTRL, 0x80 | length)        # Enable read
        time.sleep(0.01)
        return self.read_registers(0, EXT_SLV_SENS_DATA_00, length)
    
    def initialize(self):
        """Initialize the ICM20948 sensor"""
        print("Initializing ICM20948...")
        
        # Reset device
        self.write_register(0, PWR_MGMT_1, 0x80)
        time.sleep(0.1)
        
        # Wake up device and set clock source to auto-select
        self.write_register(0, PWR_MGMT_1, 0x01)
        time.sleep(0.01)
        
        # Enable accelerometer and gyroscope
        self.write_register(0, PWR_MGMT_2, 0x00)
        time.sleep(0.01)
        
        # Configure accelerometer (±2g, 1125 Hz)
        self.write_register(2, ACCEL_CONFIG, 0x00)
        time.sleep(0.01)
        
        # Configure gyroscope (±250 dps, 1125 Hz)
        self.write_register(2, GYRO_CONFIG_1, 0x00)
        time.sleep(0.01)
        
        # Enable I2C master mode
        self.write_register(0, INT_PIN_CFG, 0x02)  # Bypass enable
        time.sleep(0.01)
        
        # Configure I2C master
        self.write_register(3, I2C_MST_CTRL, 0x4D)  # I2C master mode, 400kHz
        time.sleep(0.01)
        
        # Initialize magnetometer
        self.initialize_magnetometer()
        
        print("✓ ICM20948 initialized successfully")
    
    def initialize_magnetometer(self):
        """Initialize the AK09916 magnetometer"""
        try:
            print("Initializing magnetometer...")
            
            # Check magnetometer WHO_AM_I
            who_am_i_data = self.read_mag_registers(MAG_WIA2, 1)
            if len(who_am_i_data) > 0 and who_am_i_data[0] == 0x09:
                print(f"✓ Magnetometer WHO_AM_I: 0x{who_am_i_data[0]:02X}")
            else:
                print(f"⚠ Magnetometer WHO_AM_I unexpected: {who_am_i_data}")
            
            # Reset magnetometer
            self.write_mag_register(MAG_CNTL3, 0x01)
            time.sleep(0.1)
            
            # Set continuous measurement mode (100Hz)
            self.write_mag_register(MAG_CNTL2, 0x08)
            time.sleep(0.01)
            
            self.mag_initialized = True
            print("✓ Magnetometer initialized")
            
        except Exception as e:
            print(f"⚠ Magnetometer initialization failed: {e}")
            self.mag_initialized = False
    
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
        """Read raw magnetometer data"""
        if not self.mag_initialized:
            return 0, 0, 0, False
        
        try:
            # Read status and data
            data = self.read_mag_registers(MAG_ST1, 8)
            
            if len(data) < 8:
                return 0, 0, 0, False
            
            # Check if data is ready
            if (data[0] & 0x01) == 0:
                return 0, 0, 0, False
            
            # Combine low and high bytes (note: magnetometer is little-endian)
            x = (data[2] << 8) | data[1]
            y = (data[4] << 8) | data[3]
            z = (data[6] << 8) | data[5]
            
            # Convert to signed 16-bit values
            if x > 32767: x -= 65536
            if y > 32767: y -= 65536
            if z > 32767: z -= 65536
            
            # Check overflow
            overflow = (data[7] & 0x08) != 0
            
            return x, y, z, not overflow
            
        except Exception as e:
            return 0, 0, 0, False
    
    def convert_accel(self, raw_x, raw_y, raw_z):
        """Convert raw accelerometer data to g's (±2g scale)"""
        scale = 2.0 / 32768.0
        return raw_x * scale, raw_y * scale, raw_z * scale
    
    def convert_gyro(self, raw_x, raw_y, raw_z):
        """Convert raw gyroscope data to degrees per second (±250 dps scale)"""
        scale = 250.0 / 32768.0
        return raw_x * scale, raw_y * scale, raw_z * scale
    
    def convert_mag(self, raw_x, raw_y, raw_z):
        """Convert raw magnetometer data to µT (AK09916 scale)"""
        scale = 4912.0 / 32752.0  # µT per LSB
        return raw_x * scale, raw_y * scale, raw_z * scale

def print_detailed_header():
    """Print detailed data header"""
    print("\n" + "="*100)
    print("ICM20948 9-DOF Sensor Data - Real Time")
    print("="*100)
    print("Press Ctrl+C to stop")
    print()
    print("Accelerometer (g)        Gyroscope (°/s)         Magnetometer (µT)       |Accel| |Mag|")
    print("X      Y      Z          X      Y      Z          X      Y      Z         g      µT")
    print("-"*100)

def print_comprehensive_guide():
    """Print comprehensive orientation testing guide"""
    print("\n" + "="*80)
    print("COMPREHENSIVE SENSOR ORIENTATION TEST")
    print("="*80)
    print("Follow these tests to verify all sensors are working correctly:")
    print()
    print("📊 ACCELEROMETER TEST (measures gravity + motion):")
    print("  1. Flat/level:     X≈0,  Y≈0,  Z≈+1g")
    print("  2. Upside down:    X≈0,  Y≈0,  Z≈-1g")
    print("  3. Left side down: X≈+1g, Y≈0,  Z≈0")
    print("  4. Right side down:X≈-1g, Y≈0,  Z≈0")
    print("  5. Front down:     X≈0,  Y≈+1g, Z≈0")
    print("  6. Back down:      X≈0,  Y≈-1g, Z≈0")
    print("  📍 Total magnitude should always be ≈1g when stationary")
    print()
    print("🔄 GYROSCOPE TEST (measures rotation rate):")
    print("  1. Stationary: All axes should read ≈0°/s")
    print("  2. Rotate around X-axis (roll): X changes, Y&Z≈0")
    print("  3. Rotate around Y-axis (pitch): Y changes, X&Z≈0")
    print("  4. Rotate around Z-axis (yaw): Z changes, X&Y≈0")
    print()
    print("🧭 MAGNETOMETER TEST (measures magnetic field):")
    print("  1. Should show Earth's magnetic field (~25-65µT total)")
    print("  2. Values change when you rotate the sensor")
    print("  3. Metal objects nearby will affect readings")
    print("  4. Point different directions to see X,Y,Z changes")
    print()
    print("Starting in 3 seconds... Get ready to test!")
    print("="*80)

def main():
    try:
        # Initialize sensor
        imu = ICM20948()
        
        # Show comprehensive guide
        print_comprehensive_guide()
        time.sleep(3)
        
        # Print header
        print_detailed_header()
        
        sample_count = 0
        
        while True:
            # Read all sensor data
            accel_raw = imu.read_accel_raw()
            gyro_raw = imu.read_gyro_raw()
            mag_raw_x, mag_raw_y, mag_raw_z, mag_valid = imu.read_mag_raw()
            
            # Convert to physical units
            accel_g = imu.convert_accel(*accel_raw)
            gyro_dps = imu.convert_gyro(*gyro_raw)
            
            # Calculate magnitudes
            accel_magnitude = math.sqrt(sum(x*x for x in accel_g))
            
            if mag_valid:
                mag_ut = imu.convert_mag(mag_raw_x, mag_raw_y, mag_raw_z)
                mag_magnitude = math.sqrt(sum(x*x for x in mag_ut))
                mag_status = "✓"
            else:
                mag_ut = (0, 0, 0)
                mag_magnitude = 0
                mag_status = "✗"
            
            # Print data
            print(f"{accel_g[0]:+6.2f} {accel_g[1]:+6.2f} {accel_g[2]:+6.2f}    "
                  f"{gyro_dps[0]:+7.1f} {gyro_dps[1]:+7.1f} {gyro_dps[2]:+7.1f}    "
                  f"{mag_ut[0]:+7.1f} {mag_ut[1]:+7.1f} {mag_ut[2]:+7.1f} {mag_status}    "
                  f"{accel_magnitude:5.2f}  {mag_magnitude:5.1f}", end="\r")
            
            sample_count += 1
            time.sleep(0.1)  # 10 Hz update rate
            
    except KeyboardInterrupt:
        print(f"\n\nSensor test completed! ({sample_count} samples)")
        print("\n" + "="*60)
        print("RESULTS INTERPRETATION:")
        print("="*60)
        print("✅ GOOD SIGNS:")
        print("  - Accelerometer magnitude ≈ 1.0g when stationary")
        print("  - Gyroscope ≈ 0°/s when not rotating")
        print("  - Magnetometer shows 25-65µT total magnitude")
        print("  - Values change appropriately when you move the sensor")
        print()
        print("❌ ISSUES TO CHECK:")
        print("  - If accelerometer magnitude is not ≈1g: calibration needed")
        print("  - If gyroscope doesn't read 0 when still: bias correction needed")
        print("  - If magnetometer shows ✗: initialization problem")
        print("  - If values don't change with movement: wiring/orientation issue")
        print()
        print("🎯 NEXT STEPS:")
        print("  - Implement sensor calibration routines")
        print("  - Add sensor fusion (Extended Kalman Filter)")
        print("  - Create orientation estimation algorithms")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Check connections and try again.")

if __name__ == "__main__":
    main() 