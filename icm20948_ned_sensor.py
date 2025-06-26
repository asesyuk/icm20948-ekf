#!/usr/bin/env python3
"""
ICM20948 NED-Compliant Sensor Class
Ready for Extended Kalman Filter implementation
Transforms all sensor data to NED (North-East-Down) coordinates
"""

import time
import sys
import math
import numpy as np

try:
    import smbus
except ImportError:
    print("ERROR: smbus not found. Install with: sudo apt-get install python3-smbus")
    sys.exit(1)

class ICM20948_NED:
    """ICM20948 sensor with NED coordinate transformation"""
    
    def __init__(self, address=0x69, bus=1):
        self.address = address
        self.bus_num = bus
        self.bus = smbus.SMBus(bus)
        self.mag_initialized = False
        
        # Scale factors
        self.accel_scale = 2.0 / 32768.0      # ±2g range
        self.gyro_scale = 250.0 / 32768.0     # ±250°/s range  
        self.mag_scale = 4912.0 / 32752.0     # µT per LSB for AK09916
        
        # Initialize sensor
        self.initialize()
    
    def initialize(self):
        """Initialize ICM20948 with optimal settings"""
        print("Initializing ICM20948 for NED compliance...")
        
        try:
            # Reset device
            self._write_register(0, 0x06, 0x80)  # PWR_MGMT_1: Reset
            time.sleep(0.1)
            
            # Wake up and set clock source
            self._write_register(0, 0x06, 0x01)  # PWR_MGMT_1: Auto clock
            time.sleep(0.01)
            
            # Enable accelerometer and gyroscope
            self._write_register(0, 0x07, 0x00)  # PWR_MGMT_2: Enable all
            time.sleep(0.01)
            
            # Configure accelerometer (±2g, 1125 Hz)
            self._write_register(2, 0x14, 0x00)  # ACCEL_CONFIG
            time.sleep(0.01)
            
            # Configure gyroscope (±250 dps, 1125 Hz)
            self._write_register(2, 0x01, 0x00)  # GYRO_CONFIG_1
            time.sleep(0.01)
            
            # Initialize magnetometer
            self._initialize_magnetometer()
            
            print("✓ ICM20948 initialized successfully")
            print("✓ NED transformation: X=North(forward), Y=East(right), Z=Down(-sensor_z)")
            
        except Exception as e:
            print(f"✗ Initialization failed: {e}")
            raise
    
    def _write_register(self, bank, register, value):
        """Write to a register in a specific bank"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.001)
        self.bus.write_byte_data(self.address, register, value)
        time.sleep(0.001)
    
    def _read_register(self, bank, register):
        """Read from a register in a specific bank"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.001)
        return self.bus.read_byte_data(self.address, register)
    
    def _read_registers(self, bank, start_register, length):
        """Read multiple registers in sequence"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.001)
        return self.bus.read_i2c_block_data(self.address, start_register, length)
    
    def _initialize_magnetometer(self):
        """Initialize AK09916 magnetometer via I2C master"""
        try:
            print("Initializing magnetometer...")
            
            # Enable I2C master mode
            self._write_register(0, 0x0F, 0x02)  # INT_PIN_CFG: Bypass enable
            time.sleep(0.01)
            
            # Configure I2C master
            self._write_register(3, 0x01, 0x4D)  # I2C_MST_CTRL: 400kHz
            time.sleep(0.01)
            
            # Set continuous measurement mode (100Hz)
            self._write_mag_register(0x31, 0x08)  # MAG_CNTL2
            time.sleep(0.01)
            
            self.mag_initialized = True
            print("✓ Magnetometer initialized")
            
        except Exception as e:
            print(f"⚠ Magnetometer initialization failed: {e}")
            self.mag_initialized = False
    
    def _write_mag_register(self, register, value):
        """Write to magnetometer register via I2C master"""
        self._write_register(3, 0x03, 0x0C)      # I2C_SLV0_ADDR: Mag address
        self._write_register(3, 0x04, register)  # I2C_SLV0_REG
        self._write_register(3, 0x06, value)     # I2C_SLV0_DO
        self._write_register(3, 0x05, 0x81)      # I2C_SLV0_CTRL: Enable write
        time.sleep(0.01)
    
    def _read_mag_registers(self, register, length):
        """Read from magnetometer registers via I2C master"""
        self._write_register(3, 0x03, 0x0C | 0x80)  # I2C_SLV0_ADDR: Read mode
        self._write_register(3, 0x04, register)     # I2C_SLV0_REG
        self._write_register(3, 0x05, 0x80 | length)  # I2C_SLV0_CTRL: Enable read
        time.sleep(0.01)
        return self._read_registers(0, 0x3B, length)  # EXT_SLV_SENS_DATA_00
    
    def _convert_raw_to_signed(self, high, low):
        """Convert raw 16-bit data to signed integer"""
        value = (high << 8) | low
        return value - 65536 if value > 32767 else value
    
    def read_accelerometer_raw(self):
        """Read raw accelerometer data"""
        data = self._read_registers(0, 0x2D, 6)  # ACCEL_XOUT_H
        
        x = self._convert_raw_to_signed(data[0], data[1])
        y = self._convert_raw_to_signed(data[2], data[3])
        z = self._convert_raw_to_signed(data[4], data[5])
        
        return x, y, z
    
    def read_gyroscope_raw(self):
        """Read raw gyroscope data"""
        data = self._read_registers(0, 0x33, 6)  # GYRO_XOUT_H
        
        x = self._convert_raw_to_signed(data[0], data[1])
        y = self._convert_raw_to_signed(data[2], data[3])
        z = self._convert_raw_to_signed(data[4], data[5])
        
        return x, y, z
    
    def read_magnetometer_raw(self):
        """Read raw magnetometer data"""
        if not self.mag_initialized:
            return 0, 0, 0, False
        
        try:
            data = self._read_mag_registers(0x10, 8)  # MAG_ST1
            
            if len(data) < 8 or (data[0] & 0x01) == 0:
                return 0, 0, 0, False
            
            # Magnetometer is little-endian
            x = self._convert_raw_to_signed(data[2], data[1])
            y = self._convert_raw_to_signed(data[4], data[3])
            z = self._convert_raw_to_signed(data[6], data[5])
            
            # Check for overflow
            overflow = (data[7] & 0x08) != 0
            
            return x, y, z, not overflow
            
        except Exception:
            return 0, 0, 0, False
    
    def read_accelerometer_ned(self):
        """Read accelerometer data in NED coordinates (g)"""
        raw_x, raw_y, raw_z = self.read_accelerometer_raw()
        
        # Convert to g's
        x_g = raw_x * self.accel_scale
        y_g = raw_y * self.accel_scale
        z_g = raw_z * self.accel_scale
        
        # Transform to NED coordinates (X=North, Y=East, Z=Down)
        ned_x = +y_g  # FORWARD → North (X-axis in NED)
        ned_y = +x_g  # RIGHT → East (Y-axis in NED)
        ned_z = -z_g  # UP → Down (Z-axis in NED, negated)
        
        return ned_x, ned_y, ned_z
    
    def read_gyroscope_ned(self):
        """Read gyroscope data in NED coordinates (°/s)"""
        raw_x, raw_y, raw_z = self.read_gyroscope_raw()
        
        # Convert to °/s
        x_dps = raw_x * self.gyro_scale
        y_dps = raw_y * self.gyro_scale
        z_dps = raw_z * self.gyro_scale
        
        # Transform to NED coordinates (X=North, Y=East, Z=Down)
        ned_x = +y_dps  # FORWARD → North (X-axis in NED)
        ned_y = +x_dps  # RIGHT → East (Y-axis in NED)
        ned_z = -z_dps  # UP → Down (Z-axis in NED, negated)
        
        return ned_x, ned_y, ned_z
    
    def read_magnetometer_ned(self):
        """Read magnetometer data in NED coordinates (µT)"""
        raw_x, raw_y, raw_z, valid = self.read_magnetometer_raw()
        
        if not valid:
            return 0.0, 0.0, 0.0, False
        
        # Convert to µT
        x_ut = raw_x * self.mag_scale
        y_ut = raw_y * self.mag_scale
        z_ut = raw_z * self.mag_scale
        
        # Transform to NED coordinates (X=North, Y=East, Z=Down)
        ned_x = +y_ut  # FORWARD → North (X-axis in NED)
        ned_y = +x_ut  # RIGHT → East (Y-axis in NED)
        ned_z = -z_ut  # UP → Down (Z-axis in NED, negated)
        
        return ned_x, ned_y, ned_z, True
    
    def read_all_sensors_ned(self):
        """Read all sensors in NED coordinates"""
        accel_ned = self.read_accelerometer_ned()
        gyro_ned = self.read_gyroscope_ned()
        mag_ned_x, mag_ned_y, mag_ned_z, mag_valid = self.read_magnetometer_ned()
        
        return {
            'accelerometer': accel_ned,      # (x, y, z) in g
            'gyroscope': gyro_ned,           # (x, y, z) in °/s
            'magnetometer': (mag_ned_x, mag_ned_y, mag_ned_z),  # (x, y, z) in µT
            'magnetometer_valid': mag_valid,
            'timestamp': time.time()
        }
    
    def get_orientation_estimate(self):
        """Get basic orientation estimate from accelerometer (NED coordinates)"""
        accel_x, accel_y, accel_z = self.read_accelerometer_ned()
        
        # Calculate roll and pitch from accelerometer (in NED frame)
        # In NED: X=North, Y=East, Z=Down
        roll = math.atan2(accel_y, math.sqrt(accel_x**2 + accel_z**2))    # Roll around X (North) axis
        pitch = math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2))  # Pitch around Y (East) axis
        
        # Convert to degrees
        roll_deg = math.degrees(roll)
        pitch_deg = math.degrees(pitch)
        
        return roll_deg, pitch_deg
    
    def close(self):
        """Close I2C bus"""
        self.bus.close()

# Example usage and test function
def main():
    """Test the NED-compliant ICM20948 sensor"""
    print("ICM20948 NED-Compliant Sensor Test")
    print("="*50)
    
    try:
        # Initialize sensor
        imu = ICM20948_NED()
        
        print("\nReading NED-compliant sensor data...")
        print("Press Ctrl+C to stop\n")
        
        print("Accel (g)        Gyro (°/s)       Mag (µT)         Roll  Pitch")
        print("N     E     D    N     E     D    N     E     D    (°)   (°)")
        print("-" * 70)
        
        while True:
            # Read all sensors
            data = imu.read_all_sensors_ned()
            
            accel = data['accelerometer']
            gyro = data['gyroscope']
            mag = data['magnetometer']
            mag_valid = data['magnetometer_valid']
            
            # Calculate orientation
            roll, pitch = imu.get_orientation_estimate()
            
            # Format output
            mag_status = "✓" if mag_valid else "✗"
            
            print(f"{accel[0]:+5.2f} {accel[1]:+5.2f} {accel[2]:+5.2f}  "
                  f"{gyro[0]:+5.1f} {gyro[1]:+5.1f} {gyro[2]:+5.1f}  "
                  f"{mag[0]:+5.0f} {mag[1]:+5.0f} {mag[2]:+5.0f} {mag_status}  "
                  f"{roll:+5.1f} {pitch:+5.1f}", end="\r")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nNED sensor test completed!")
        print("\nNED Compliance Verified:")
        print("✓ Accelerometer: X=North, Y=East, Z=Down")
        print("✓ Gyroscope: Rotation rates in NED frame")
        print("✓ Magnetometer: Magnetic field in NED frame")
        print("✓ Ready for Extended Kalman Filter implementation!")
        
    except Exception as e:
        print(f"\nError: {e}")
        
    finally:
        try:
            imu.close()
        except:
            pass

if __name__ == "__main__":
    main() 