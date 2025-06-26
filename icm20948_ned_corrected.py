#!/usr/bin/env python3
"""
ICM20948 NED-Compliant Sensor Class - CORRECTED for Your Mounting
Based on your test results showing 90-degree rotation
Transforms all sensor data to NED (North-East-Down) coordinates
"""

import time
import sys
import math

try:
    import smbus
except ImportError:
    print("ERROR: smbus not found. Install with: sudo apt-get install python3-smbus")
    sys.exit(1)

class ICM20948_NED_Corrected:
    """ICM20948 sensor with corrected NED coordinate transformation for your mounting"""
    
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
        print("Initializing ICM20948 with CORRECTED NED transformation...")
        
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
            print("✓ NED transformation corrected based on your test results:")
            print("  ACCELEROMETER:")
            print("    X_ned = +X_sensor  (your 'right' direction → North)")
            print("    Y_ned = +Y_sensor  (your 'forward' direction → East)")
            print("    Z_ned = -Z_sensor  (up → Down)")
            print("  GYROSCOPE:")
            print("    X_ned = -X_sensor  (your 'right' rotation → North)")
            print("    Y_ned = -Y_sensor  (your 'forward' rotation → East)")
            print("    Z_ned = +Z_sensor  (up rotation → Down)")
            print("  MAGNETOMETER:")
            print("    X_ned = -X_sensor  (your 'right' direction → North, negated)")
            print("    Y_ned = -Y_sensor  (your 'forward' direction → East, negated)")
            print("    Z_ned = -Z_sensor  (up → Down)")
            
        except Exception as e:
            print(f"✗ Initialization failed: {e}")
            raise
    
    def _write_register(self, bank, register, value):
        """Write to a register in a specific bank"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.002)  # Increased delay for better reliability
        self.bus.write_byte_data(self.address, register, value)
        time.sleep(0.002)  # Increased delay for better reliability
    
    def _read_register(self, bank, register):
        """Read from a register in a specific bank"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.002)  # Increased delay for better reliability
        return self.bus.read_byte_data(self.address, register)
    
    def _read_registers(self, bank, start_register, length):
        """Read multiple registers in sequence"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.002)  # Increased delay for better reliability
        return self.bus.read_i2c_block_data(self.address, start_register, length)
    
    def _initialize_magnetometer(self):
        """Initialize AK09916 magnetometer via I2C master - IMPROVED"""
        try:
            print("Initializing magnetometer...")
            
            # Step 1: Configure I2C master first
            self._write_register(3, 0x01, 0x4D)  # I2C_MST_CTRL: 400kHz
            time.sleep(0.02)
            
            # Step 2: Use I2C master mode (not bypass) - this method worked in debug
            self._write_register(0, 0x0F, 0x00)  # INT_PIN_CFG: Disable bypass
            time.sleep(0.02)
            
            # Enable I2C master
            self._write_register(0, 0x03, 0x20)  # USER_CTRL: I2C master enable
            time.sleep(0.02)
            
            # Step 3: Test magnetometer communication
            self._write_register(3, 0x03, 0x0C | 0x80)  # I2C_SLV0_ADDR: Read mode
            self._write_register(3, 0x04, 0x01)         # I2C_SLV0_REG: WHO_AM_I
            self._write_register(3, 0x05, 0x81)         # I2C_SLV0_CTRL: Enable read, 1 byte
            time.sleep(0.1)  # Longer wait for I2C master
            
            who_am_i = self._read_register(0, 0x3B)  # Read result
            
            if who_am_i != 0x09:
                print(f"⚠ Magnetometer WHO_AM_I: 0x{who_am_i:02X} (expected 0x09)")
                print("  Run 'python3 fix_magnetometer_continuous.py' to fix this")
                self.mag_initialized = False
                return
            
            # Step 4: Reset magnetometer
            self._write_mag_register(0x32, 0x01)  # CNTL3: Reset
            time.sleep(0.2)  # Longer reset wait
            
            # Step 5: Set power down mode first (required by AK09916)
            self._write_mag_register(0x31, 0x00)  # CNTL2: Power down
            time.sleep(0.1)
            
            # Step 6: Set continuous measurement mode 2 (50Hz) - more stable than 100Hz
            self._write_mag_register(0x31, 0x06)  # CNTL2: Continuous mode 2
            time.sleep(0.1)
            
            # Step 7: Verify mode setting
            mode_data = self._read_mag_registers(0x31, 1)
            if len(mode_data) > 0:
                mode = mode_data[0]
                if mode == 0x06:
                    self.mag_initialized = True
                    print("✓ Magnetometer initialized successfully (50Hz continuous mode)")
                else:
                    print(f"⚠ Failed to set magnetometer mode (got 0x{mode:02X}, expected 0x06)")
                    print("  Run 'python3 fix_magnetometer_continuous.py' to fix this")
                    self.mag_initialized = False
            else:
                print("⚠ Failed to verify magnetometer mode")
                print("  Run 'python3 fix_magnetometer_continuous.py' to fix this")
                self.mag_initialized = False
            
        except Exception as e:
            print(f"⚠ Magnetometer initialization failed: {e}")
            print("  Run 'python3 fix_magnetometer_continuous.py' to fix this")
            self.mag_initialized = False
    
    def _write_mag_register(self, register, value):
        """Write to magnetometer register via I2C master"""
        self._write_register(3, 0x03, 0x0C)      # I2C_SLV0_ADDR: Mag address
        self._write_register(3, 0x04, register)  # I2C_SLV0_REG
        self._write_register(3, 0x06, value)     # I2C_SLV0_DO
        self._write_register(3, 0x05, 0x81)      # I2C_SLV0_CTRL: Enable write
        time.sleep(0.03)  # Increased delay for magnetometer communication
    
    def _read_mag_registers(self, register, length):
        """Read from magnetometer registers via I2C master"""
        self._write_register(3, 0x03, 0x0C | 0x80)  # I2C_SLV0_ADDR: Read mode
        self._write_register(3, 0x04, register)     # I2C_SLV0_REG
        self._write_register(3, 0x05, 0x80 | length)  # I2C_SLV0_CTRL: Enable read
        time.sleep(0.03)  # Increased delay for magnetometer communication
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
        """Read raw magnetometer data - IMPROVED for continuous mode"""
        if not self.mag_initialized:
            return 0, 0, 0, False
        
        try:
            # Read ST1 register first to check data ready
            st1_data = self._read_mag_registers(0x10, 1)
            if len(st1_data) < 1:
                return 0, 0, 0, False
            
            st1 = st1_data[0]
            
            # Check if new data is ready (bit 0 = 1)
            if (st1 & 0x01) == 0:
                return 0, 0, 0, False
            
            # Read magnetometer data (6 bytes: HXL, HXH, HYL, HYH, HZL, HZH)
            data = self._read_mag_registers(0x11, 6)
            
            if len(data) < 6:
                return 0, 0, 0, False
            
            # Magnetometer is little-endian
            x = self._convert_raw_to_signed(data[1], data[0])  # HXH, HXL
            y = self._convert_raw_to_signed(data[3], data[2])  # HYH, HYL
            z = self._convert_raw_to_signed(data[5], data[4])  # HZH, HZL
            
            # Read ST2 register to complete the reading sequence and clear data ready
            st2_data = self._read_mag_registers(0x18, 1)
            if len(st2_data) > 0:
                st2 = st2_data[0]
                # Check for overflow (bit 3 = 1 means overflow)
                overflow = (st2 & 0x08) != 0
            else:
                overflow = False
            
            return x, y, z, not overflow
            
        except Exception as e:
            return 0, 0, 0, False
    
    def read_accelerometer_ned(self):
        """Read accelerometer data in NED coordinates (g) - CORRECTED"""
        raw_x, raw_y, raw_z = self.read_accelerometer_raw()
        
        # Convert to g's
        x_g = raw_x * self.accel_scale
        y_g = raw_y * self.accel_scale
        z_g = raw_z * self.accel_scale
        
        # CORRECTED NED transformation based on your test results
        ned_x = +x_g  # Your RIGHT direction → North (X-axis in NED)
        ned_y = +y_g  # Your FORWARD direction → East (Y-axis in NED)
        ned_z = -z_g  # UP → Down (Z-axis in NED, negated)
        
        return ned_x, ned_y, ned_z
    
    def read_gyroscope_ned(self):
        """Read gyroscope data in NED coordinates (°/s) - CORRECTED"""
        raw_x, raw_y, raw_z = self.read_gyroscope_raw()
        
        # Convert to °/s
        x_dps = raw_x * self.gyro_scale
        y_dps = raw_y * self.gyro_scale
        z_dps = raw_z * self.gyro_scale
        
        # CORRECTED NED transformation for GYROSCOPE (different from accelerometer!)
        ned_x = -x_dps  # Your RIGHT rotation → North (X-axis in NED, negated)
        ned_y = -y_dps  # Your FORWARD rotation → East (Y-axis in NED, negated)
        ned_z = +z_dps  # UP rotation → Down (Z-axis in NED, no negation)
        
        return ned_x, ned_y, ned_z
    
    def read_magnetometer_ned(self):
        """Read magnetometer data in NED coordinates (µT) - CORRECTED"""
        raw_x, raw_y, raw_z, valid = self.read_magnetometer_raw()
        
        if not valid:
            return 0.0, 0.0, 0.0, False
        
        # Convert to µT
        x_ut = raw_x * self.mag_scale
        y_ut = raw_y * self.mag_scale
        z_ut = raw_z * self.mag_scale
        
        # CORRECTED NED transformation for MAGNETOMETER (opposite signs from accelerometer!)
        ned_x = -x_ut  # Your RIGHT direction → North (X-axis in NED, negated)
        ned_y = -y_ut  # Your FORWARD direction → East (Y-axis in NED, negated)
        ned_z = -z_ut  # UP → Down (Z-axis in NED, negated)
        
        return ned_x, ned_y, ned_z, True
    
    def read_all_sensors_ned(self):
        """Read all sensors in NED coordinates - CORRECTED"""
        accel_ned = self.read_accelerometer_ned()
        gyro_ned = self.read_gyroscope_ned()
        mag_ned_x, mag_ned_y, mag_ned_z, mag_valid = self.read_magnetometer_ned()
        
        return {
            'accelerometer': accel_ned,      # (North, East, Down) in g
            'gyroscope': gyro_ned,           # (North, East, Down) in °/s
            'magnetometer': (mag_ned_x, mag_ned_y, mag_ned_z),  # (North, East, Down) in µT
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

# Test function to verify the corrected transformation
def main():
    """Test the corrected NED-compliant ICM20948 sensor"""
    print("ICM20948 CORRECTED NED Sensor Test")
    print("="*50)
    
    try:
        # Initialize sensor
        imu = ICM20948_NED_Corrected()
        
        print("\nTesting corrected transformation...")
        print("Try tilting your sensor to verify the correction:")
        print("- Tilt FORWARD: X_ned should now be positive")
        print("- Tilt RIGHT: Y_ned should now be positive")
        print("- Level: Z_ned should be positive (~1g)")
        print("\nPress Ctrl+C to stop\n")
        
        print("Accel (g)        Gyro (°/s)       Roll  Pitch")
        print("N     E     D    N     E     D    (°)   (°)")
        print("-" * 60)
        
        while True:
            # Read all sensors
            data = imu.read_all_sensors_ned()
            
            accel = data['accelerometer']
            gyro = data['gyroscope']
            
            # Calculate orientation
            roll, pitch = imu.get_orientation_estimate()
            
            print(f"{accel[0]:+5.2f} {accel[1]:+5.2f} {accel[2]:+5.2f}  "
                  f"{gyro[0]:+5.1f} {gyro[1]:+5.1f} {gyro[2]:+5.1f}  "
                  f"{roll:+5.1f} {pitch:+5.1f}", end="\r")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nCorrected NED sensor test completed!")
        print("\nWith the corrected transformations:")
        print("✓ ACCELEROMETER:")
        print("  X_ned = +X_sensor, Y_ned = +Y_sensor, Z_ned = -Z_sensor")
        print("✓ GYROSCOPE:")
        print("  X_ned = -X_sensor, Y_ned = -Y_sensor, Z_ned = +Z_sensor")
        print("✓ MAGNETOMETER:")
        print("  X_ned = -X_sensor, Y_ned = -Y_sensor, Z_ned = -Z_sensor")
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