# 📋 ICM20948 Calibration Coordinate Systems - Critical Understanding

## 🔍 **The Issue You Discovered**

You asked an excellent question: **"What XYZ coordinates are we using for calibration?"**

The answer revealed a **fundamental mistake** in the original calibration approach.

## 🚨 **WRONG Approach (Original)**

```
Raw Sensor → NED Transformation → Calibration ❌
```

The original `calibrate_all_sensors.py` was working with **NED-transformed coordinates**:
- `imu.read_accelerometer_ned()` ← Already transformed!
- `imu.read_gyroscope_ned()` ← Already transformed!
- `imu.read_magnetometer_ned()` ← Already transformed!

### **Why This Is Wrong:**

1. **Calibration parameters should correct sensor physics**, not coordinate systems
2. **NED transformation assumes perfect sensors** - but we're calibrating imperfect ones!
3. **Bias and scale errors are properties of the physical sensor**, not the transformed coordinates

### **This Explains Your "Abnormalities":**

- **Z accelerometer bias = +2.003g** → This is gravity in transformed coordinates!
- **Scale factor error = 201%** → Transformation distorting calibration measurements
- **High gyroscope noise** → Artificially inflated by coordinate transformation

## ✅ **CORRECT Approach (Fixed)**

```
Raw Sensor → Calibration Correction → NED Transformation → EKF Input ✅
```

The new `calibrate_raw_sensors.py` works with **raw sensor coordinates**:
- `imu.read_accelerometer_raw()` ← Pure sensor readings!
- `imu.read_gyroscope_raw()` ← Pure sensor readings!
- `imu.read_magnetometer_raw()` ← Pure sensor readings!

## 📊 **Coordinate System Comparison**

| Aspect | Raw Sensor Coordinates | NED-Transformed Coordinates |
|--------|----------------------|---------------------------|
| **X-axis** | Physical sensor X-axis | North direction |
| **Y-axis** | Physical sensor Y-axis | East direction |
| **Z-axis** | Physical sensor Z-axis | Down direction |
| **Bias** | True sensor offset | Transformed offset (misleading) |
| **Scale** | True sensor scaling | Transformed scaling (misleading) |
| **Calibration** | ✅ Correct place | ❌ Wrong place |

## 🔧 **Proper Data Flow**

### **Step 1: Raw Sensor Reading**
```python
raw_x, raw_y, raw_z = sensor.read_raw()
# These are the true physical sensor readings
```

### **Step 2: Apply Calibration**
```python
# Remove bias
calibrated_x = raw_x - bias_x
calibrated_y = raw_y - bias_y  
calibrated_z = raw_z - bias_z

# Apply scale factors
calibrated_x *= scale_x
calibrated_y *= scale_y
calibrated_z *= scale_z
```

### **Step 3: Apply NED Transformation**
```python
# Transform to NED coordinates
ned_x = +calibrated_x  # For accelerometer (example)
ned_y = +calibrated_y  # For accelerometer
ned_z = -calibrated_z  # For accelerometer
```

### **Step 4: Use in EKF**
```python
# Now ready for Extended Kalman Filter
ekf.update(ned_x, ned_y, ned_z)
```

## 📁 **File Usage Guide**

### **Use for EKF Implementation:**
- **`calibrate_raw_sensors.py`** ← ✅ **USE THIS ONE!**
- **`icm20948_raw_calibration.json`** ← Output from correct calibration

### **Deprecated (Reference Only):**
- **`calibrate_all_sensors.py`** ← ⚠️ Contains coordinate system error
- **`icm20948_calibration.json`** ← Invalid calibration data

## 🎯 **Implementation Notes**

### **For EKF Integration:**

1. **Read raw sensor data**
2. **Apply calibration parameters from `icm20948_raw_calibration.json`**
3. **Then apply NED transformations**
4. **Feed corrected NED data to EKF**

### **Example Code:**
```python
# Step 1: Read raw
raw_accel = imu.read_accelerometer_raw()

# Step 2: Apply calibration
cal_data = load_calibration("icm20948_raw_calibration.json")
accel_calibrated = apply_calibration(raw_accel, cal_data['accelerometer'])

# Step 3: Transform to NED
accel_ned = transform_to_ned(accel_calibrated, 'accelerometer')

# Step 4: Use in EKF
ekf.predict_and_update(accel_ned, gyro_ned, mag_ned)
```

## 💡 **Key Takeaway**

**Calibration must happen in the sensor's native coordinate system, not in the transformed coordinate system!**

Your question revealed a fundamental architectural issue that would have caused significant problems in EKF implementation. The corrected approach will provide much more accurate sensor fusion results.

## 🔍 **Verification**

After running the corrected calibration, you should see:
- **Much smaller bias values** (especially for accelerometer Z-axis)
- **Realistic scale factors** (close to 1.0)
- **Lower abnormality counts**
- **More stable sensor readings**

This is the difference between calibrating the **physical sensor** vs. calibrating the **mathematical transformation**! 