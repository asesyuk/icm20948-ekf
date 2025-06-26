#!/usr/bin/env python3
"""
ICM20948 I2C Connection Test Script
This script verifies that the ICM20948 IMU is properly connected via I2C
"""

import time
import sys

try:
    import smbus
except ImportError:
    print("ERROR: smbus module not found. Install with: sudo apt-get install python3-smbus")
    sys.exit(1)

# ICM20948 I2C addresses (7-bit)
ICM20948_I2C_ADDR_1 = 0x69  # AD0 pin high (your configuration)
ICM20948_I2C_ADDR_2 = 0x68  # AD0 pin low (default)

# ICM20948 Register addresses
WHO_AM_I_REG = 0x00
WHO_AM_I_EXPECTED = 0xEA  # Expected value for ICM20948

# Bank selection register
REG_BANK_SEL = 0x7F

def check_i2c_device(bus, address):
    """Check if a device responds at the given I2C address"""
    try:
        bus.read_byte(address)
        return True
    except OSError:
        return False

def read_register(bus, address, register):
    """Read a single byte from a register"""
    try:
        return bus.read_byte_data(address, register)
    except OSError as e:
        print(f"Error reading register 0x{register:02X}: {e}")
        return None

def write_register(bus, address, register, value):
    """Write a single byte to a register"""
    try:
        bus.write_byte_data(address, register, value)
        return True
    except OSError as e:
        print(f"Error writing to register 0x{register:02X}: {e}")
        return False

def check_icm20948_connection():
    """Main function to check ICM20948 connection"""
    print("ICM20948 I2C Connection Test")
    print("=" * 40)
    
    # Initialize I2C bus (usually bus 1 on Raspberry Pi)
    try:
        bus = smbus.SMBus(1)
        print("✓ I2C bus 1 initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize I2C bus: {e}")
        return False
    
    # Check both possible I2C addresses
    addresses_to_check = [ICM20948_I2C_ADDR_1, ICM20948_I2C_ADDR_2]
    icm_address = None
    
    print("\nScanning for ICM20948...")
    for addr in addresses_to_check:
        print(f"Checking address 0x{addr:02X}...", end=" ")
        if check_i2c_device(bus, addr):
            print("✓ Device found!")
            icm_address = addr
            break
        else:
            print("✗ No response")
    
    if icm_address is None:
        print("\n✗ ICM20948 not found on I2C bus!")
        print("Troubleshooting tips:")
        print("- Check wiring connections (SDA, SCL, VCC, GND)")
        print("- Verify I2C is enabled: sudo raspi-config > Interface Options > I2C")
        print("- Check if other I2C devices are present: i2cdetect -y 1")
        print("- Try different I2C bus: change SMBus(1) to SMBus(0)")
        return False
    
    print(f"\n✓ ICM20948 found at address 0x{icm_address:02X}")
    
    # Set bank 0 to access WHO_AM_I register
    print("\nSetting register bank to 0...")
    if not write_register(bus, icm_address, REG_BANK_SEL, 0x00):
        print("✗ Failed to set register bank")
        return False
    
    time.sleep(0.01)  # Small delay after bank switch
    
    # Read WHO_AM_I register
    print("Reading WHO_AM_I register...")
    who_am_i = read_register(bus, icm_address, WHO_AM_I_REG)
    
    if who_am_i is None:
        print("✗ Failed to read WHO_AM_I register")
        return False
    
    print(f"WHO_AM_I register value: 0x{who_am_i:02X}")
    
    if who_am_i == WHO_AM_I_EXPECTED:
        print("✓ WHO_AM_I register matches expected value (0xEA)")
        print("✓ ICM20948 is properly connected and responding!")
        return True
    else:
        print(f"✗ WHO_AM_I mismatch! Expected 0x{WHO_AM_I_EXPECTED:02X}, got 0x{who_am_i:02X}")
        print("This might not be an ICM20948 or there's a communication issue.")
        return False

def scan_i2c_bus():
    """Scan and display all devices on I2C bus"""
    print("\nI2C Bus Scan:")
    print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
    
    try:
        bus = smbus.SMBus(1)
        for row in range(0, 8):
            print(f"{row}0: ", end="")
            for col in range(0, 16):
                address = row * 16 + col
                if address < 0x03 or address > 0x77:
                    print("   ", end="")
                elif check_i2c_device(bus, address):
                    print(f"{address:02x} ", end="")
                else:
                    print("-- ", end="")
            print()
    except Exception as e:
        print(f"Error scanning I2C bus: {e}")

if __name__ == "__main__":
    print("Starting ICM20948 connection test...\n")
    
    # First scan the I2C bus
    scan_i2c_bus()
    
    # Then specifically test ICM20948
    print("\n" + "=" * 50)
    success = check_icm20948_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ CONNECTION TEST PASSED - ICM20948 is working!")
    else:
        print("✗ CONNECTION TEST FAILED - Please check connections")
    
    print("\nNext steps:")
    if success:
        print("- You can now proceed with ICM20948 data reading")
        print("- Consider testing accelerometer, gyroscope, and magnetometer")
    else:
        print("- Verify wiring: VCC to 3.3V, GND to GND, SDA to GPIO 2, SCL to GPIO 3")
        print("- Enable I2C: sudo raspi-config > Interface Options > I2C > Enable")
        print("- Install I2C tools: sudo apt-get install i2c-tools")
        print("- Run: i2cdetect -y 1 to see all I2C devices") 