#!/usr/bin/env python3
"""
ICM20948 Magnetometer Continuous Mode Fix
Fix the magnetometer to properly work in continuous measurement mode
"""

import time
import sys

try:
    import smbus
except ImportError:
    print("ERROR: smbus not found. Install with: sudo apt-get install python3-smbus")
    sys.exit(1)

class ICM20948_MagFix:
    """Fix ICM20948 magnetometer continuous mode"""
    
    def __init__(self, address=0x69, bus=1):
        self.address = address
        self.bus_num = bus
        self.bus = smbus.SMBus(bus)
        self.mag_initialized = False
    
    def _write_register(self, bank, register, value):
        """Write to a register in a specific bank"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, register, value)
        time.sleep(0.005)
    
    def _read_register(self, bank, register):
        """Read from a register in a specific bank"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.005)
        return self.bus.read_byte_data(self.address, register)
    
    def _read_registers(self, bank, start_register, length):
        """Read multiple registers in sequence"""
        self.bus.write_byte_data(self.address, 0x7F, bank << 4)  # Set bank
        time.sleep(0.005)
        return self.bus.read_i2c_block_data(self.address, start_register, length)
    
    def initialize_basic(self):
        """Initialize basic ICM20948"""
        print("🔧 Initializing basic ICM20948...")
        
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
    
    def setup_i2c_master_for_magnetometer(self):
        """Set up I2C master for magnetometer access"""
        print("🔧 Setting up I2C master for magnetometer...")
        
        # Configure I2C master (400kHz)
        self._write_register(3, 0x01, 0x4D)  # I2C_MST_CTRL: 400kHz
        time.sleep(0.02)
        
        # Disable bypass, enable I2C master
        self._write_register(0, 0x0F, 0x00)  # INT_PIN_CFG: Disable bypass
        time.sleep(0.02)
        
        # Enable I2C master
        self._write_register(0, 0x03, 0x20)  # USER_CTRL: I2C master enable
        time.sleep(0.02)
        
        print("✅ I2C master configured")
    
    def _write_mag_register(self, register, value):
        """Write to magnetometer register via I2C master"""
        print(f"  Writing mag reg 0x{register:02X} = 0x{value:02X}")
        self._write_register(3, 0x03, 0x0C)      # I2C_SLV0_ADDR: Mag write address
        self._write_register(3, 0x04, register)  # I2C_SLV0_REG
        self._write_register(3, 0x06, value)     # I2C_SLV0_DO: Data to write
        self._write_register(3, 0x05, 0x81)      # I2C_SLV0_CTRL: Enable write, 1 byte
        time.sleep(0.1)  # Wait for write to complete
    
    def _read_mag_register(self, register):
        """Read from magnetometer register via I2C master"""
        self._write_register(3, 0x03, 0x0C | 0x80)  # I2C_SLV0_ADDR: Mag read address
        self._write_register(3, 0x04, register)     # I2C_SLV0_REG
        self._write_register(3, 0x05, 0x81)         # I2C_SLV0_CTRL: Enable read, 1 byte
        time.sleep(0.1)  # Wait for read to complete
        return self._read_register(0, 0x3B)  # Read result from EXT_SLV_SENS_DATA_00
    
    def _read_mag_data_block(self, register, length):
        """Read multiple magnetometer registers"""
        self._write_register(3, 0x03, 0x0C | 0x80)        # I2C_SLV0_ADDR: Mag read address
        self._write_register(3, 0x04, register)           # I2C_SLV0_REG
        self._write_register(3, 0x05, 0x80 | length)      # I2C_SLV0_CTRL: Enable read, multiple bytes
        time.sleep(0.1)  # Wait for read to complete
        return self._read_registers(0, 0x3B, length)  # Read results
    
    def initialize_magnetometer_continuous(self):
        """Initialize magnetometer in proper continuous mode"""
        print("🧭 Initializing magnetometer in continuous mode...")
        
        # Step 1: Check WHO_AM_I
        who_am_i = self._read_mag_register(0x01)
        print(f"  WHO_AM_I: 0x{who_am_i:02X} (should be 0x09)")
        
        if who_am_i != 0x09:
            print("❌ Magnetometer not responding")
            return False
        
        # Step 2: Soft reset magnetometer
        print("  Resetting magnetometer...")
        self._write_mag_register(0x32, 0x01)  # CNTL3: Soft reset
        time.sleep(0.2)  # Wait for reset
        
        # Step 3: Set to power-down mode first (required before mode change)
        print("  Setting power-down mode...")
        self._write_mag_register(0x31, 0x00)  # CNTL2: Power down
        time.sleep(0.1)
        
        # Verify power-down
        mode = self._read_mag_register(0x31)
        print(f"  Power-down mode: 0x{mode:02X} (should be 0x00)")
        
        # Step 4: Set continuous measurement mode 2 (50Hz) - more stable than 100Hz
        print("  Setting continuous mode 2 (50Hz)...")
        self._write_mag_register(0x31, 0x06)  # CNTL2: Continuous mode 2
        time.sleep(0.1)
        
        # Verify continuous mode
        mode = self._read_mag_register(0x31)
        print(f"  Continuous mode: 0x{mode:02X} (should be 0x06)")
        
        if mode != 0x06:
            print("❌ Failed to set continuous mode")
            return False
        
        # Step 5: Wait for first measurement
        print("  Waiting for first measurement...")
        time.sleep(0.2)
        
        print("✅ Magnetometer initialized in continuous mode")
        self.mag_initialized = True
        return True
    
    def test_continuous_readings(self):
        """Test that magnetometer is providing continuous readings"""
        print("\n🧪 Testing continuous magnetometer readings...")
        print("ST1   |   X      Y      Z   | Status")
        print("------|---------------------|-------")
        
        for i in range(20):
            # Read ST1 (status) register
            st1 = self._read_mag_register(0x10)
            
            # Read magnetometer data
            data = self._read_mag_data_block(0x11, 6)  # HXL to HZH
            
            if len(data) >= 6:
                # Convert to signed 16-bit (little-endian)
                x = (data[1] << 8) | data[0]
                y = (data[3] << 8) | data[2]
                z = (data[5] << 8) | data[4]
                
                # Convert to signed
                if x > 32767: x -= 65536
                if y > 32767: y -= 65536
                if z > 32767: z -= 65536
                
                # Check data ready bit
                data_ready = (st1 & 0x01) != 0
                status = "READY" if data_ready else "NOT READY"
                
                print(f"0x{st1:02X}  | {x:+6d} {y:+6d} {z:+6d} | {status}")
                
                # Read ST2 to clear the data ready flag
                st2 = self._read_mag_register(0x18)
                
            else:
                print(f"0x{st1:02X}  | Read failed           | ERROR")
            
            time.sleep(0.1)  # 10Hz reading rate
        
        print("\n📊 Analysis:")
        print("Look for:")
        print("• ST1 should toggle between 0x01 (data ready) and 0x00")
        print("• X, Y, Z values should change when you rotate the sensor")
        print("• No identical consecutive readings")
    
    def close(self):
        """Close I2C bus"""
        self.bus.close()

def main():
    """Main magnetometer fix function"""
    print("🔧 ICM20948 Magnetometer Continuous Mode Fix")
    print("=" * 55)
    
    try:
        mag_fix = ICM20948_MagFix()
        
        # Initialize basic ICM20948
        mag_fix.initialize_basic()
        
        # Set up I2C master
        mag_fix.setup_i2c_master_for_magnetometer()
        
        # Initialize magnetometer in continuous mode
        if mag_fix.initialize_magnetometer_continuous():
            print("\n🎉 SUCCESS! Magnetometer is now in continuous mode!")
            
            # Test continuous readings
            mag_fix.test_continuous_readings()
            
            print("\n✅ If you see changing readings, the magnetometer is working!")
            print("You can now run: python3 test_magnetometer_ned_directions.py")
        else:
            print("\n❌ Failed to initialize magnetometer in continuous mode")
            print("Check hardware connections and try again")
        
    except Exception as e:
        print(f"\nError: {e}")
        
    finally:
        try:
            mag_fix.close()
        except:
            pass

if __name__ == "__main__":
    main() 