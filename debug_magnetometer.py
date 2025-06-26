#!/usr/bin/env python3
"""
ICM20948 Magnetometer Debugging Script
Diagnose and fix magnetometer initialization issues
"""

import time
import sys

try:
    import smbus
except ImportError:
    print("ERROR: smbus not found. Install with: sudo apt-get install python3-smbus")
    sys.exit(1)

class ICM20948_MagDebug:
    """Debug ICM20948 magnetometer initialization"""
    
    def __init__(self, address=0x69, bus=1):
        self.address = address
        self.bus_num = bus
        self.bus = smbus.SMBus(bus)
        self.mag_initialized = False
    
    def _write_register(self, bank, register, value):
        """Write to a register in a specific bank"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.005)  # Increased delay
        self.bus.write_byte_data(self.address, register, value)
        time.sleep(0.005)  # Increased delay
    
    def _read_register(self, bank, register):
        """Read from a register in a specific bank"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.005)  # Increased delay
        return self.bus.read_byte_data(self.address, register)
    
    def _read_registers(self, bank, start_register, length):
        """Read multiple registers in sequence"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.005)  # Increased delay
        return self.bus.read_i2c_block_data(self.address, start_register, length)
    
    def initialize_basic(self):
        """Initialize basic ICM20948 (accelerometer and gyroscope)"""
        print("🔧 Initializing basic ICM20948...")
        
        try:
            # Reset device
            self._write_register(0, 0x06, 0x80)  # PWR_MGMT_1: Reset
            time.sleep(0.1)
            
            # Wake up and set clock source
            self._write_register(0, 0x06, 0x01)  # PWR_MGMT_1: Auto clock
            time.sleep(0.05)
            
            # Enable accelerometer and gyroscope
            self._write_register(0, 0x07, 0x00)  # PWR_MGMT_2: Enable all
            time.sleep(0.05)
            
            print("✅ Basic ICM20948 initialized")
            return True
            
        except Exception as e:
            print(f"❌ Basic initialization failed: {e}")
            return False
    
    def debug_magnetometer_step_by_step(self):
        """Debug magnetometer initialization step by step"""
        print("\n🔍 MAGNETOMETER DEBUGGING:")
        print("=" * 40)
        
        try:
            # Step 1: Check I2C Master configuration
            print("Step 1: Checking I2C Master configuration...")
            
            # Read current I2C master control
            i2c_mst_ctrl = self._read_register(3, 0x01)
            print(f"  Current I2C_MST_CTRL: 0x{i2c_mst_ctrl:02X}")
            
            # Configure I2C master (400kHz)
            self._write_register(3, 0x01, 0x4D)  
            time.sleep(0.05)
            
            # Verify configuration
            i2c_mst_ctrl = self._read_register(3, 0x01)
            print(f"  Set I2C_MST_CTRL to: 0x{i2c_mst_ctrl:02X}")
            
            # Step 2: Enable I2C master mode
            print("Step 2: Enabling I2C master mode...")
            
            # Method 1: Try bypass mode first
            self._write_register(0, 0x0F, 0x02)  # INT_PIN_CFG: Bypass enable
            time.sleep(0.05)
            
            # Check if bypass worked
            int_pin_cfg = self._read_register(0, 0x0F)
            print(f"  INT_PIN_CFG set to: 0x{int_pin_cfg:02X}")
            
            # Step 3: Try to access magnetometer directly
            print("Step 3: Attempting direct magnetometer access...")
            
            # Try to read magnetometer WHO_AM_I (should be 0x09)
            try:
                # Configure to read from magnetometer WHO_AM_I register (0x01)
                self._write_register(3, 0x03, 0x0C | 0x80)  # I2C_SLV0_ADDR: Read mode
                self._write_register(3, 0x04, 0x01)         # I2C_SLV0_REG: WHO_AM_I
                self._write_register(3, 0x05, 0x81)         # I2C_SLV0_CTRL: Enable read, 1 byte
                time.sleep(0.1)  # Wait for read
                
                # Read the result
                mag_who_am_i = self._read_register(0, 0x3B)  # EXT_SLV_SENS_DATA_00
                print(f"  Magnetometer WHO_AM_I: 0x{mag_who_am_i:02X} (should be 0x09)")
                
                if mag_who_am_i == 0x09:
                    print("✅ Magnetometer communication working!")
                    
                    # Step 4: Try different initialization sequence
                    print("Step 4: Trying enhanced initialization sequence...")
                    
                    # Reset magnetometer
                    self._write_mag_register(0x32, 0x01)  # CNTL3: Reset
                    time.sleep(0.1)
                    
                    # Set to power down mode first
                    self._write_mag_register(0x31, 0x00)  # CNTL2: Power down
                    time.sleep(0.05)
                    
                    # Set to continuous measurement mode 4 (100Hz)
                    self._write_mag_register(0x31, 0x08)  # CNTL2: Continuous 4
                    time.sleep(0.05)
                    
                    # Verify mode setting
                    mode = self._read_mag_register(0x31, 1)[0]
                    print(f"  Magnetometer mode set to: 0x{mode:02X} (should be 0x08)")
                    
                    if mode == 0x08:
                        print("✅ Magnetometer initialized successfully!")
                        self.mag_initialized = True
                        return True
                    else:
                        print("❌ Failed to set magnetometer mode")
                        
                else:
                    print("❌ Magnetometer communication failed")
                    print("   Trying alternative I2C master setup...")
                    
                    # Alternative method: Use I2C master mode instead of bypass
                    self._write_register(0, 0x0F, 0x00)  # Disable bypass
                    time.sleep(0.05)
                    
                    # Enable I2C master
                    self._write_register(0, 0x03, 0x20)  # USER_CTRL: I2C master enable
                    time.sleep(0.05)
                    
                    # Try reading WHO_AM_I again
                    self._write_register(3, 0x03, 0x0C | 0x80)  # I2C_SLV0_ADDR: Read mode
                    self._write_register(3, 0x04, 0x01)         # I2C_SLV0_REG: WHO_AM_I
                    self._write_register(3, 0x05, 0x81)         # I2C_SLV0_CTRL: Enable read, 1 byte
                    time.sleep(0.1)
                    
                    mag_who_am_i = self._read_register(0, 0x3B)
                    print(f"  Alternative method - WHO_AM_I: 0x{mag_who_am_i:02X}")
                    
                    if mag_who_am_i == 0x09:
                        print("✅ Alternative method worked!")
                        # Continue with initialization...
                        self._write_mag_register(0x31, 0x08)
                        time.sleep(0.05)
                        self.mag_initialized = True
                        return True
                        
            except Exception as e:
                print(f"❌ Error accessing magnetometer: {e}")
            
            return False
            
        except Exception as e:
            print(f"❌ Debug failed: {e}")
            return False
    
    def _write_mag_register(self, register, value):
        """Write to magnetometer register via I2C master"""
        self._write_register(3, 0x03, 0x0C)      # I2C_SLV0_ADDR: Mag address (write)
        self._write_register(3, 0x04, register)  # I2C_SLV0_REG
        self._write_register(3, 0x06, value)     # I2C_SLV0_DO
        self._write_register(3, 0x05, 0x81)      # I2C_SLV0_CTRL: Enable write, 1 byte
        time.sleep(0.05)  # Increased delay
    
    def _read_mag_register(self, register, length):
        """Read from magnetometer register via I2C master"""
        self._write_register(3, 0x03, 0x0C | 0x80)  # I2C_SLV0_ADDR: Read mode
        self._write_register(3, 0x04, register)     # I2C_SLV0_REG
        self._write_register(3, 0x05, 0x80 | length)  # I2C_SLV0_CTRL: Enable read
        time.sleep(0.05)  # Increased delay
        return self._read_registers(0, 0x3B, length)  # EXT_SLV_SENS_DATA_00
    
    def test_magnetometer_reading(self):
        """Test reading magnetometer data"""
        if not self.mag_initialized:
            print("❌ Magnetometer not initialized")
            return False
        
        print("\n🧪 Testing magnetometer readings...")
        
        try:
            for i in range(10):
                # Read magnetometer data
                data = self._read_mag_register(0x11, 7)  # ST1 + XYZ data + ST2
                
                if len(data) >= 7:
                    st1 = data[0]
                    mag_x = (data[2] << 8) | data[1]  # Little endian
                    mag_y = (data[4] << 8) | data[3]
                    mag_z = (data[6] << 8) | data[5]
                    
                    # Convert to signed
                    if mag_x > 32767: mag_x -= 65536
                    if mag_y > 32767: mag_y -= 65536
                    if mag_z > 32767: mag_z -= 65536
                    
                    print(f"  Reading {i+1}: ST1=0x{st1:02X} X={mag_x:+6d} Y={mag_y:+6d} Z={mag_z:+6d}")
                    
                    if st1 & 0x01:  # Data ready
                        print("✅ Magnetometer data valid!")
                        return True
                else:
                    print(f"  Reading {i+1}: Insufficient data")
                
                time.sleep(0.1)
            
            print("❌ No valid magnetometer readings")
            return False
            
        except Exception as e:
            print(f"❌ Error reading magnetometer: {e}")
            return False
    
    def close(self):
        """Close I2C bus"""
        self.bus.close()

def main():
    """Main magnetometer debugging function"""
    print("🔍 ICM20948 Magnetometer Debug Tool")
    print("=" * 50)
    
    try:
        debug = ICM20948_MagDebug()
        
        # Step 1: Initialize basic sensors
        if not debug.initialize_basic():
            print("❌ Failed to initialize basic ICM20948")
            return
        
        # Step 2: Debug magnetometer step by step
        if debug.debug_magnetometer_step_by_step():
            print("\n🎉 Magnetometer debugging successful!")
            
            # Step 3: Test readings
            if debug.test_magnetometer_reading():
                print("\n✅ MAGNETOMETER WORKING!")
                print("You can now use the magnetometer in your NED tests.")
            else:
                print("\n⚠️  Magnetometer initialized but readings may be unstable")
        else:
            print("\n❌ MAGNETOMETER DEBUGGING FAILED")
            print("\nPossible issues:")
            print("• Hardware connection problem")
            print("• Magnetic interference")
            print("• ICM20948 firmware issue")
            print("• I2C communication problem")
        
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        
    finally:
        try:
            debug.close()
        except:
            pass

if __name__ == "__main__":
    main() 