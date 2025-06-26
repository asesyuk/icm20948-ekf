# ICM20948 I2C Connection Test

This repository contains tools to verify that your ICM20948 IMU is properly connected to your Raspberry Pi via I2C.

## Files

- `check_icm20948_connection.py` - Comprehensive Python script for testing ICM20948 connectivity
- `check_i2c_commands.sh` - Shell script with basic I2C detection commands
- `README.md` - This instruction file

## Prerequisites

### On your Raspberry Pi:

1. **Enable I2C interface:**
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options > I2C > Enable
   sudo reboot
   ```

2. **Install required packages:**
   ```bash
   sudo apt-get update
   sudo apt-get install i2c-tools python3-smbus
   ```

## Wiring

Connect your ICM20948 to the Raspberry Pi as follows:

| ICM20948 Pin | Raspberry Pi Pin | GPIO |
|--------------|------------------|------|
| VCC/VDD      | Pin 1 (3.3V)     | -    |
| GND          | Pin 6 (GND)      | -    |
| SDA          | Pin 3            | GPIO 2 |
| SCL          | Pin 5            | GPIO 3 |
| AD0          | GND (0x68) or 3.3V (0x69) | - |

## How to Use

### Method 1: Transfer files to Raspberry Pi

1. **Copy files to your Raspberry Pi:**
   ```bash
   # From your Mac/local machine
   scp check_icm20948_connection.py pi@your-pi-ip:~/
   scp check_i2c_commands.sh pi@your-pi-ip:~/
   ```

2. **SSH into your Raspberry Pi:**
   ```bash
   ssh pi@your-pi-ip
   ```

3. **Run the Python test script:**
   ```bash
   python3 check_icm20948_connection.py
   ```

4. **Or run the shell script:**
   ```bash
   chmod +x check_i2c_commands.sh
   ./check_i2c_commands.sh
   ```

### Method 2: Quick I2C check (directly on Pi)

If you just want to quickly check without transferring files:

```bash
# Scan I2C bus for devices
i2cdetect -y 1

# Check WHO_AM_I register (should return 0xea for ICM20948)
# For address 0x68:
i2cget -y 1 0x68 0x00

# For address 0x69:
i2cget -y 1 0x69 0x00
```

## Expected Results

### Successful Connection
```
I2C Bus Scan:
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --

✓ ICM20948 found at address 0x68
✓ WHO_AM_I register matches expected value (0xEA)
✓ ICM20948 is properly connected and responding!
```

### Common Issues and Solutions

1. **No device found on I2C bus:**
   - Check wiring connections
   - Ensure I2C is enabled: `sudo raspi-config`
   - Try different I2C bus: change `SMBus(1)` to `SMBus(0)` in Python script

2. **Permission denied errors:**
   - Add user to i2c group: `sudo usermod -a -G i2c pi`
   - Log out and back in

3. **WHO_AM_I mismatch:**
   - Verify you have an ICM20948 (not ICM20602 or other variant)
   - Check for wiring issues or interference

4. **I2C tools not found:**
   ```bash
   sudo apt-get install i2c-tools python3-smbus
   ```

## Next Steps

Once your ICM20948 is verified as connected:
- You can proceed with reading accelerometer, gyroscope, and magnetometer data
- Consider implementing an Extended Kalman Filter for sensor fusion
- Set up continuous data logging and processing

## ICM20948 I2C Addresses

- `0x68` (104 decimal) - when AD0 pin is connected to GND (default)
- `0x69` (105 decimal) - when AD0 pin is connected to VCC

## 🚨 **Important Calibration Discovery**

**CRITICAL:** A fundamental coordinate system issue was discovered in the calibration approach:

- **❌ WRONG:** `calibrate_all_sensors.py` - Calibrates AFTER NED transformation
- **✅ CORRECT:** `calibrate_raw_sensors.py` - Calibrates RAW sensor data first

**Why this matters:**
- Calibration should correct **physical sensor imperfections**
- NED transformation should be applied **after** calibration
- The wrong approach gives false abnormalities (like 2g Z-bias = gravity!)

📋 **Use `calibrate_raw_sensors.py` for proper EKF-ready calibration.**
📖 **Read `CALIBRATION_COORDINATE_SYSTEMS.md` for detailed explanation.**

## Current Status
- ✅ All 9-DOF sensors working in proper NED coordinates
- ✅ Magnetometer continuous mode functioning  
- ✅ Corrected calibration suite ready for EKF implementation
- ⚠️ Coordinate system calibration issue identified and resolved

## Troubleshooting Tips

- Always use 3.3V, not 5V (ICM20948 is not 5V tolerant)
- Ensure proper pull-up resistors on SDA/SCL (usually built into Pi)
- Check for loose connections
- Try a different I2C bus if available
- Use `dmesg | grep i2c` to check for I2C-related kernel messages 