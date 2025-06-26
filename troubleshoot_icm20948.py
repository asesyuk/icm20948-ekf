#!/usr/bin/env python3
"""
ICM20948 Troubleshooting Script
Helps diagnose connection issues with ICM20948 IMU
"""

import time
import subprocess
import sys

try:
    import smbus
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False

def run_command(cmd):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_i2c_enabled():
    """Check if I2C is enabled on the system"""
    print("1. Checking I2C Status")
    print("-" * 30)
    
    # Check if I2C modules are loaded
    success, stdout, stderr = run_command("lsmod | grep i2c")
    if success and stdout:
        print("✓ I2C modules loaded:")
        for line in stdout.split('\n'):
            if 'i2c' in line:
                print(f"  {line}")
    else:
        print("✗ I2C modules not found")
        print("  Solution: Enable I2C with 'sudo raspi-config'")
        return False
    
    # Check I2C device files
    success, stdout, stderr = run_command("ls -la /dev/i2c*")
    if success and stdout:
        print("✓ I2C device files found:")
        for line in stdout.split('\n'):
            if '/dev/i2c' in line:
                print(f"  {line}")
    else:
        print("✗ No I2C device files found")
        return False
    
    return True

def check_i2c_tools():
    """Check if I2C tools are installed"""
    print("\n2. Checking I2C Tools")
    print("-" * 30)
    
    tools = ['i2cdetect', 'i2cget', 'i2cset']
    all_available = True
    
    for tool in tools:
        success, stdout, stderr = run_command(f"which {tool}")
        if success:
            print(f"✓ {tool} available at {stdout}")
        else:
            print(f"✗ {tool} not found")
            all_available = False
    
    if not all_available:
        print("  Solution: Install with 'sudo apt-get install i2c-tools'")
    
    return all_available

def scan_all_i2c_buses():
    """Scan all available I2C buses"""
    print("\n3. Scanning All I2C Buses")
    print("-" * 30)
    
    # Find available I2C buses
    success, stdout, stderr = run_command("ls /dev/i2c-*")
    if not success:
        print("✗ No I2C buses found")
        return []
    
    buses = []
    for line in stdout.split('\n'):
        if '/dev/i2c-' in line:
            bus_num = line.split('-')[-1]
            buses.append(int(bus_num))
    
    print(f"Found I2C buses: {buses}")
    
    devices_found = {}
    for bus in buses:
        print(f"\nScanning bus {bus}:")
        success, stdout, stderr = run_command(f"i2cdetect -y {bus}")
        if success:
            print(stdout)
            # Parse for devices
            devices = []
            lines = stdout.split('\n')[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) > 1:
                    for addr in parts[1:]:
                        if addr != '--' and len(addr) == 2:
                            try:
                                devices.append(int(addr, 16))
                            except ValueError:
                                pass
            devices_found[bus] = devices
            if devices:
                print(f"Devices found on bus {bus}: {[hex(d) for d in devices]}")
            else:
                print(f"No devices found on bus {bus}")
        else:
            print(f"✗ Failed to scan bus {bus}: {stderr}")
    
    return devices_found

def test_icm20948_addresses(devices_found):
    """Test specific ICM20948 addresses"""
    print("\n4. Testing ICM20948 Addresses")
    print("-" * 30)
    
    icm_addresses = [0x68, 0x69]
    found_icm = False
    
    for bus, devices in devices_found.items():
        for addr in icm_addresses:
            print(f"\nTesting bus {bus}, address 0x{addr:02x}:")
            
            if addr in devices:
                print(f"  ✓ Device responds at 0x{addr:02x}")
                
                # Try to read WHO_AM_I register
                success, stdout, stderr = run_command(f"i2cget -y {bus} 0x{addr:02x} 0x00")
                if success:
                    who_am_i = stdout.strip()
                    print(f"  WHO_AM_I register: {who_am_i}")
                    if who_am_i.lower() == "0xea":
                        print(f"  ✓ ICM20948 confirmed at bus {bus}, address 0x{addr:02x}!")
                        found_icm = True
                    else:
                        print(f"  ✗ WHO_AM_I mismatch (expected 0xea, got {who_am_i})")
                        print(f"  This might be a different device")
                else:
                    print(f"  ✗ Failed to read WHO_AM_I: {stderr}")
                    print(f"  The device responds but communication failed")
            else:
                print(f"  ✗ No device at 0x{addr:02x}")
    
    return found_icm

def check_python_smbus():
    """Check Python smbus availability"""
    print("\n5. Checking Python SMBus")
    print("-" * 30)
    
    if SMBUS_AVAILABLE:
        print("✓ Python smbus module available")
        try:
            bus = smbus.SMBus(1)
            print("✓ Successfully opened I2C bus 1")
            bus.close()
        except Exception as e:
            print(f"✗ Failed to open I2C bus 1: {e}")
            return False
    else:
        print("✗ Python smbus module not available")
        print("  Solution: Install with 'sudo apt-get install python3-smbus'")
        return False
    
    return True

def check_permissions():
    """Check I2C permissions"""
    print("\n6. Checking I2C Permissions")
    print("-" * 30)
    
    # Check current user groups
    success, stdout, stderr = run_command("groups")
    if success:
        groups = stdout.split()
        if 'i2c' in groups:
            print("✓ User is in i2c group")
        else:
            print("✗ User not in i2c group")
            print("  Solution: sudo usermod -a -G i2c $USER")
            print("  Then log out and back in")
    
    # Check I2C device permissions
    success, stdout, stderr = run_command("ls -la /dev/i2c*")
    if success:
        print("I2C device permissions:")
        for line in stdout.split('\n'):
            if '/dev/i2c' in line:
                print(f"  {line}")

def print_wiring_guide():
    """Print wiring guide"""
    print("\n7. Wiring Guide")
    print("-" * 30)
    print("Double-check your wiring:")
    print("ICM20948 → Raspberry Pi")
    print("VCC/VDD → Pin 1 (3.3V) - NEVER use 5V!")
    print("GND     → Pin 6 (GND)")
    print("SDA     → Pin 3 (GPIO 2)")
    print("SCL     → Pin 5 (GPIO 3)")
    print("AD0     → GND (for 0x68) or 3.3V (for 0x69)")
    print("\nCommon issues:")
    print("- Loose connections")
    print("- Wrong voltage (5V instead of 3.3V)")
    print("- Swapped SDA/SCL")
    print("- Bad breadboard contacts")

def print_next_steps(found_icm):
    """Print next steps"""
    print("\n" + "=" * 50)
    if found_icm:
        print("✓ ICM20948 FOUND AND WORKING!")
        print("\nNext steps:")
        print("- Run the full connection test: python3 check_icm20948_connection.py")
        print("- Start reading sensor data")
        print("- Implement sensor fusion algorithms")
    else:
        print("✗ ICM20948 NOT FOUND")
        print("\nTroubleshooting steps:")
        print("1. Double-check all wiring connections")
        print("2. Ensure I2C is enabled: sudo raspi-config")
        print("3. Try a different I2C bus if available")
        print("4. Test with a simple I2C device first")
        print("5. Check if the ICM20948 is working (try different board)")
        print("6. Verify 3.3V power supply stability")

def main():
    """Main troubleshooting function"""
    print("ICM20948 I2C Troubleshooting")
    print("=" * 50)
    
    # Step 1: Check I2C enabled
    if not check_i2c_enabled():
        print("\n⚠️  I2C is not properly enabled. Enable it first!")
        return
    
    # Step 2: Check I2C tools
    if not check_i2c_tools():
        print("\n⚠️  I2C tools missing. Install them first!")
        return
    
    # Step 3: Scan buses
    devices_found = scan_all_i2c_buses()
    
    # Step 4: Test ICM20948 addresses
    found_icm = test_icm20948_addresses(devices_found)
    
    # Step 5: Check Python smbus
    check_python_smbus()
    
    # Step 6: Check permissions
    check_permissions()
    
    # Step 7: Show wiring guide
    print_wiring_guide()
    
    # Final summary
    print_next_steps(found_icm)

if __name__ == "__main__":
    main() 