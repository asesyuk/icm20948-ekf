# ICM20948 Sensor Testing Guide

## Overview
Your ICM20948 is successfully connected at address **0x69**! Now let's test all sensors and verify their orientation.

## Available Test Scripts

### 1. `test_icm20948_0x69.py` - Basic Connection Test
**Purpose:** Verify the sensor is working and read a sample of accelerometer data.

```bash
python3 test_icm20948_0x69.py
```

**What it does:**
- Confirms ICM20948 connection
- Reads WHO_AM_I register
- Shows basic accelerometer values

### 2. `quick_orientation_test.py` - Quick Orientation Check ⭐ **START HERE**
**Purpose:** Simple real-time test to verify sensor orientation is correct.

```bash
python3 quick_orientation_test.py
```

**What to expect:**
- Real-time accelerometer and gyroscope data
- Automatic orientation detection
- Perfect for verifying axes are correct

### 3. `icm20948_sensor_test.py` - Full Sensor Test
**Purpose:** Comprehensive test with detailed orientation guide.

```bash
python3 icm20948_sensor_test.py
```

**What it includes:**
- Accelerometer, gyroscope readings
- Detailed orientation testing instructions
- Magnitude calculations

### 4. `icm20948_full_sensor.py` - Complete 9-DOF Test
**Purpose:** Full test including magnetometer (if working).

```bash
python3 icm20948_full_sensor.py
```

**What it includes:**
- All 9 degrees of freedom (accel, gyro, magnetometer)
- Complete sensor initialization
- I2C master setup for magnetometer

## Step-by-Step Testing Process

### Step 1: Basic Connection Test
```bash
python3 test_icm20948_0x69.py
```
✅ **Expected result:** "ICM20948 is connected and working!"

### Step 2: Quick Orientation Test
```bash
python3 quick_orientation_test.py
```

#### Test Positions (NED Coordinate System):
**Your sensor orientation:** X=LEFT, Y=FORWARD, Z=?

1. **Flat on table:**
   - Expected: |Z| ≈ 1.0g, X ≈ 0g, Y ≈ 0g
   - If Z is negative → Z points DOWN (NED compliant)
   - If Z is positive → Z points UP (needs inversion for NED)

2. **Tilt LEFT (X-axis down):**
   - Expected: X ≈ +1.0g, Y ≈ 0g, Z ≈ 0g
   - Display: "TILTED LEFT - X+ pointing DOWN"

3. **Tilt RIGHT (opposite of X-axis down):**
   - Expected: X ≈ -1.0g, Y ≈ 0g, Z ≈ 0g
   - Display: "TILTED RIGHT - X- pointing DOWN"

4. **Tilt FORWARD (Y-axis down):**
   - Expected: Y ≈ +1.0g, X ≈ 0g, Z ≈ 0g
   - Display: "TILTED FORWARD - Y+ pointing DOWN"

5. **Tilt BACKWARD (opposite of Y-axis down):**
   - Expected: Y ≈ -1.0g, X ≈ 0g, Z ≈ 0g
   - Display: "TILTED BACKWARD - Y- pointing DOWN"

#### Gyroscope Test:
- **Stationary:** All axes should read ≈ 0°/s
- **Rotate around X-axis:** X value changes, Y & Z stay near 0
- **Rotate around Y-axis:** Y value changes, X & Z stay near 0
- **Rotate around Z-axis:** Z value changes, X & Y stay near 0

### Step 3: Comprehensive Test
```bash
python3 icm20948_full_sensor.py
```

This will test magnetometer as well and provide the most complete sensor verification.

## What Good Results Look Like

### ✅ Accelerometer (Good):
- **Magnitude always ≈ 1.0g when stationary**
- **Values change correctly with orientation**
- **Smooth, stable readings**

### ✅ Gyroscope (Good):
- **≈ 0°/s when not moving**
- **Spikes when rotating**
- **Returns to 0 when rotation stops**

### ✅ Magnetometer (Good):
- **Total magnitude ≈ 25-65µT (Earth's magnetic field)**
- **Values change when rotating sensor**
- **Consistent readings**

## Troubleshooting

### ❌ Issues and Solutions:

#### **Accelerometer magnitude not ≈ 1g:**
- **Problem:** Scale factor incorrect or sensor needs calibration
- **Solution:** Check if using correct ±2g scale

#### **Wrong orientation responses:**
- **Problem:** Axes are swapped or inverted
- **Solution:** Check if chip orientation matches expected coordinate system

#### **Gyroscope doesn't read 0 when still:**
- **Problem:** Gyroscope bias (normal, needs calibration)
- **Solution:** Implement bias correction (subtract average stationary reading)

#### **Magnetometer not working:**
- **Problem:** I2C master initialization failed
- **Solution:** Run full sensor script which has better magnetometer setup

#### **Noisy readings:**
- **Problem:** Electrical interference or loose connections
- **Solution:** Check wiring, add capacitors, move away from electrical noise

## Your Sensor Coordinate System (NED Compatible)

```
NED Coordinate System:
- North: Forward
- East: Right  
- Down: Toward Earth

Your Physical Sensor:
     Y (FORWARD/North)
     ↑
     |
     |
X ←--+--→ -X (RIGHT/East)
(LEFT)|
     |
     ↓
    -Y (BACKWARD)

Z-axis direction: To be determined by testing
- If Z+ points DOWN → NED compliant
- If Z+ points UP → Invert Z for NED compliance

Expected for NED:
- X: LEFT is positive (West direction)
- Y: FORWARD is positive (North direction)  
- Z: DOWN is positive (toward Earth)
```

## Next Steps After Successful Testing

1. **✅ Sensor Calibration**
   - Accelerometer bias and scale correction
   - Gyroscope bias removal
   - Magnetometer hard/soft iron correction

2. **✅ Sensor Fusion**
   - Extended Kalman Filter implementation
   - Complementary filter
   - Attitude estimation

3. **✅ Data Logging**
   - Continuous data capture
   - CSV export for analysis
   - Real-time plotting

## Quick Reference Commands

```bash
# Transfer all files to Pi (run from Mac)
./transfer_to_pi.sh

# On Raspberry Pi:
python3 quick_orientation_test.py      # Start here!
python3 icm20948_full_sensor.py        # Complete test
python3 test_icm20948_0x69.py          # Basic connection only
```

## Support

If you encounter issues:
1. Check wiring (especially power: 3.3V NOT 5V!)
2. Verify I2C is enabled: `sudo raspi-config`
3. Check address: `i2cdetect -y 1` (should see device at 0x69)
4. Run diagnostics: `python3 troubleshoot_icm20948.py`

Your ICM20948 is working at **address 0x69** - you're ready to test! 🚀 