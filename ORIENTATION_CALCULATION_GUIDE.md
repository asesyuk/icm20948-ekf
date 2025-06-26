# 🧭 ICM20948 Orientation Calculation from Calibrated Data

## 📋 **Overview**

The `orientation_from_calibrated_data.py` script calculates **yaw, pitch, and roll** angles using properly calibrated ICM20948 sensor data **without using an EKF**. This is an important intermediate step before implementing a full Extended Kalman Filter.

## 🔄 **Data Flow**

```
Raw Sensor Data → Apply Calibration → NED Transform → Calculate Orientation
```

This is the **correct approach** - calibration happens **before** coordinate transformation.

## 🎯 **What It Calculates**

### **1. Accelerometer-Based Orientation**
- **Roll**: Bank angle (rotation around North axis) - positive when right wing down
- **Pitch**: Elevation angle (rotation around East axis) - positive when nose up
- Uses gravity vector to determine absolute orientation

### **2. Magnetometer-Based Orientation**  
- **Yaw**: Heading angle (rotation around Down axis) - 0° = North, 90° = East
- Uses magnetic field vector with **tilt compensation**
- Corrects for magnetic declination (adjustable for your location)

### **3. Gyroscope Integration**
- **Roll, Pitch, Yaw**: Integrated from angular rates
- Provides smooth motion tracking but **drifts over time**
- Useful for short-term orientation changes

## 📊 **Sensor Characteristics**

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Accelerometer** | Absolute orientation, no drift | Affected by motion/vibration | Static measurements |
| **Magnetometer** | Absolute heading, no drift | Magnetic interference | Heading when stationary |
| **Gyroscope** | Smooth, fast response | Drifts over time | Motion tracking |

## 🎯 **Prerequisites**

1. **ICM20948 connected and working**
2. **Corrected calibration file exists**: `icm20948_raw_calibration.json`
3. **Numpy installed on Pi**: `sudo apt install python3-numpy`

## 📱 **Usage**

### **On Your Raspberry Pi:**

```bash
# 1. SSH to your Pi
ssh pi@192.168.156.102

# 2. Run the orientation calculator
python3 orientation_from_calibrated_data.py
```

## 📊 **Output Display**

```
ACCELEROMETER     MAGNETOMETER    GYRO INTEGRATION  
Roll  Pitch       Yaw (Mag)       Roll  Pitch  Yaw
(°)   (°)         (°)             (°)   (°)    (°)
---------------------------------------------------------
+12.3 -5.1        247.8           +12.1 -5.2   248.2
```

### **Understanding the Output:**

- **Accelerometer Roll/Pitch**: Absolute angles from gravity
- **Magnetometer Yaw**: Absolute heading from magnetic field  
- **Gyro Integration**: Integrated angles (will drift)

## 🔧 **How It Works**

### **Step 1: Load Calibration**
```python
# Loads icm20948_raw_calibration.json
calibration_data = json.load("icm20948_raw_calibration.json")
```

### **Step 2: Read Raw Sensors**
```python
accel_raw = imu.read_accelerometer_raw()    # Raw sensor values
gyro_raw = imu.read_gyroscope_raw()
mag_raw = imu.read_magnetometer_raw()
```

### **Step 3: Apply Calibration**
```python
# Remove bias and apply scale factors
accel_cal = (accel_raw - bias) * scale_factors
gyro_cal = gyro_raw - bias  
mag_cal = (mag_raw - hard_iron) * soft_iron
```

### **Step 4: Transform to NED**
```python
# Apply your specific sensor mounting transformations
accel_ned = [+accel_cal[0], +accel_cal[1], -accel_cal[2]]  # Accelerometer
gyro_ned = [-gyro_cal[0], -gyro_cal[1], +gyro_cal[2]]      # Gyroscope  
mag_ned = [-mag_cal[0], -mag_cal[1], -mag_cal[2]]          # Magnetometer
```

### **Step 5: Calculate Orientation**
```python
# Roll and Pitch from accelerometer
roll = atan2(ay, sqrt(ax² + az²))
pitch = atan2(-ax, sqrt(ay² + az²))

# Yaw from magnetometer (with tilt compensation)
yaw = atan2(-mag_y_comp, mag_x_comp) + magnetic_declination
```

## 🎛️ **Configuration Options**

### **Magnetic Declination**
Adjust for your location in the script:
```python
self.magnetic_declination = 0.0  # degrees
# Example: 
# San Francisco: +13.8°
# New York: -13.2°  
# London: +0.3°
```

Find your local declination at: https://www.magnetic-declination.com/

## 🔍 **Verification Steps**

### **Test Each Method:**

1. **Accelerometer Test**: Tilt sensor and verify roll/pitch match physical orientation
2. **Magnetometer Test**: Point sensor North and verify yaw ≈ 0° (or 360°)
3. **Gyroscope Test**: Rotate sensor and watch smooth angle changes

### **Expected Behavior:**

- **Static**: Accelerometer and magnetometer should give stable readings
- **Motion**: Gyroscope should track motion smoothly
- **Drift**: Gyroscope will slowly drift away from absolute values

## 🚨 **Troubleshooting**

### **No Calibration File**
```bash
❌ Calibration file icm20948_raw_calibration.json not found
   Run: python3 calibrate_raw_sensors.py
```
**Solution**: Run the corrected calibration script first.

### **Magnetometer Shows N/A**
```bash
Yaw (Mag): N/A
```
**Solution**: Run `python3 fix_magnetometer_continuous.py`

### **Large Differences Between Methods**
- **Accelerometer vs Gyro**: Normal during motion
- **Magnetometer vs Others**: Check for magnetic interference
- **All methods wrong**: Check calibration quality

## 💡 **Why This is Important**

This script demonstrates the **proper data processing pipeline** for EKF implementation:

1. **Validates calibration**: Ensures calibrated data makes sense
2. **Tests coordinate transformations**: Verifies NED conversion is correct  
3. **Shows sensor limitations**: Highlights why sensor fusion (EKF) is needed
4. **Provides reference**: Ground truth for EKF comparison

## 🚀 **Next Steps**

After verifying orientation calculation works correctly:

1. **Analyze sensor behavior** under different conditions
2. **Note drift rates** and noise characteristics  
3. **Identify when each sensor is most reliable**
4. **Design EKF** to optimally combine all three sources

## 📁 **Related Files**

- **`calibrate_raw_sensors.py`**: Creates the calibration file
- **`icm20948_ned_corrected.py`**: Sensor interface class
- **`CALIBRATION_COORDINATE_SYSTEMS.md`**: Explains calibration approach
- **EKF implementation**: Coming next!

## 🎯 **Key Insights**

- **Accelerometer**: Great for absolute roll/pitch when stationary
- **Magnetometer**: Essential for absolute yaw/heading  
- **Gyroscope**: Provides smooth motion but needs correction
- **Sensor Fusion**: EKF will optimally combine all advantages

This script bridges the gap between raw sensor calibration and full EKF implementation! 