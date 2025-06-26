# NED Orientation Verification Test Guide

## 🧭 **Correct NED Convention**

This test verifies the **standard navigation NED (North-East-Down)** coordinate system:

- **X-axis = NORTH** (Forward direction) ✅
- **Y-axis = EAST** (Right direction) ✅  
- **Z-axis = DOWN** (Toward Earth) ✅

## 📊 **Transformation Applied**

The test applies the correct ICM20948 → NED transformation:

```python
# NED Transformation (X=North, Y=East, Z=Down)
X_ned = +Y_sensor  # FORWARD → North (X-axis in NED)
Y_ned = +X_sensor  # RIGHT → East (Y-axis in NED)
Z_ned = -Z_sensor  # UP → Down (Z-axis in NED, negated)
```

## 🚀 **How to Run the Test**

### Transfer and Run:
```bash
# Transfer all files to your Pi
./transfer_to_pi.sh

# SSH to your Pi
ssh pi@your-pi-ip

# Run the NED verification test
python3 ned_orientation_verification.py
```

## 🧪 **Test Modes**

### **1. Interactive Orientation Test (Recommended)**
**Purpose:** Step-by-step verification of NED orientation

**What it does:**
- Guides you through 5 specific orientation tests
- Measures accelerometer readings for each position
- Validates that readings match NED expectations
- Provides pass/fail results for each test

**Test Sequence:**
1. **Level Test**: Sensor flat → Z_ned ≈ +1g
2. **Forward Tilt**: Tilt forward → X_ned positive 
3. **Backward Tilt**: Tilt backward → X_ned negative
4. **Right Tilt**: Tilt right → Y_ned positive
5. **Left Tilt**: Tilt left → Y_ned negative

### **2. Continuous Monitoring Mode**
**Purpose:** Real-time NED coordinate display

**What it shows:**
- Live accelerometer and gyroscope data in NED coordinates
- Current orientation (Level, Tilted Forward, etc.)
- Acceleration magnitude for reference

### **3. Combined Mode**
**Purpose:** Interactive test followed by continuous monitoring

## 📋 **Expected Results**

### **✅ Correct NED Behavior:**

| Position | X_ned (North) | Y_ned (East) | Z_ned (Down) | Status |
|----------|---------------|--------------|--------------|---------|
| **Level** | ≈ 0g | ≈ 0g | ≈ +1g | ✓ |
| **Forward Tilt** | **Positive** | ≈ 0g | < 1g | ✓ |
| **Backward Tilt** | **Negative** | ≈ 0g | < 1g | ✓ |
| **Right Tilt** | ≈ 0g | **Positive** | < 1g | ✓ |
| **Left Tilt** | ≈ 0g | **Negative** | < 1g | ✓ |

### **Sample Output:**
```
Test 1/5: Level Test
Instruction: Place the sensor FLAT and LEVEL on a table
Expected: Z_ned (Down) should be ~+1.0g, X_ned and Y_ned should be ~0g
Press Enter when ready...
Results: X_ned=-0.02g  Y_ned=+0.01g  Z_ned=+1.00g
Orientation: LEVEL (Down is positive - correct NED)
Test Result: ✓ PASS
```

## 🎯 **Interpretation Guide**

### **Passing Results (4-5/5 tests):**
```
🎉 EXCELLENT! Your NED orientation is correctly configured!
✓ Ready for Extended Kalman Filter implementation
```

**Action:** Proceed with confidence to EKF implementation!

### **Mostly Correct (3/5 tests):**
```
⚠️ MOSTLY CORRECT - Minor adjustments may be needed
Check the failed tests and verify your coordinate system
```

**Action:** Review failed tests, check physical mounting

### **Failed Results (0-2/5 tests):**
```
❌ ORIENTATION ISSUES DETECTED
Please check your sensor mounting and transformation matrix
```

**Action:** 
1. Check physical sensor mounting
2. Verify vehicle coordinate system
3. Run `orientation_guidance.py` for custom transformation

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **Wrong Forward Direction:**
- **Symptom:** Forward/Backward tilt tests fail
- **Solution:** Ensure +Y_sensor points in your vehicle's forward direction

#### **Wrong Right Direction:**
- **Symptom:** Right/Left tilt tests fail  
- **Solution:** Ensure +X_sensor points in your vehicle's right direction

#### **Inverted Z-axis:**
- **Symptom:** Level test shows Z_ned ≈ -1g instead of +1g
- **Solution:** Check if sensor is mounted upside down

#### **Swapped Axes:**
- **Symptom:** Tilt tests pass but in wrong directions
- **Solution:** Verify transformation matrix matches your mounting

### **Debug Mode:**
The continuous monitoring mode shows both sensor and NED values, helping identify transformation issues.

## 📖 **Understanding NED for EKF**

### **Why NED Matters:**
- **Standard Convention:** Most navigation algorithms expect NED
- **EKF Compatibility:** Kalman filters assume consistent coordinate systems
- **Integration:** GPS, INS, and other navigation systems use NED

### **EKF State Vector (typical):**
```python
state = [
    roll,     # Rotation around X_ned (North) axis
    pitch,    # Rotation around Y_ned (East) axis  
    yaw,      # Rotation around Z_ned (Down) axis
    # ... other states
]
```

### **Process Model:**
```python
# Attitude kinematics with NED gyroscope rates
gyro_ned = [gyro_x_north, gyro_y_east, gyro_z_down]
attitude_rate = f(attitude, gyro_ned)
```

### **Measurement Models:**
```python
# Gravity vector in NED frame
gravity_ned = [0, 0, +1]  # Down is positive

# Expected accelerometer reading when level
h_accel = R_body_to_ned.T @ gravity_ned
```

## ✅ **Pre-EKF Checklist**

After passing the NED verification test:

- [ ] ✅ **Orientation verified:** X=North, Y=East, Z=Down
- [ ] ✅ **Sensor readings:** Match expected NED behavior  
- [ ] ✅ **Transformation confirmed:** Correct coordinate conversion
- [ ] ✅ **Documentation:** Understanding of NED convention
- [ ] ✅ **Test results:** 4-5/5 tests passing

**You're ready for Extended Kalman Filter implementation!** 🚀

## 🔗 **Related Files**

- `icm20948_ned_sensor.py` - NED-compliant sensor class
- `orientation_guidance.py` - Custom orientation determination
- `READY_FOR_EKF.md` - Complete EKF readiness guide
- `MOUNTING_GUIDE.md` - Physical mounting instructions

Your ICM20948 sensor system is now mathematically correct and ready for serious navigation applications! 