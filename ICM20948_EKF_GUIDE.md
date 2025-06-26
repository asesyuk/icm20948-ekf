# 🎯 ICM20948 Extended Kalman Filter - Complete Implementation Guide

## 🚀 **Overview**

The `icm20948_ekf.py` script implements a **complete Extended Kalman Filter** for optimal orientation estimation using your calibrated ICM20948 sensor. This is the **final culmination** of all the work we've done together.

## 🎯 **What This Solves**

Remember the problems you discovered with manual gyroscope integration:
- ❌ **Sharp movements** caused large errors requiring resets
- ❌ **Gyroscope drift** accumulated over time  
- ❌ **Manual intervention** needed for correction
- ❌ **No optimal sensor fusion** between accelerometer, gyroscope, and magnetometer

**The EKF solves ALL of these issues!** 🎉

## 🧠 **EKF State Vector**

The EKF estimates a **6-dimensional state**:
```python
state = [
    roll,     # Orientation around North axis (rad)
    pitch,    # Orientation around East axis (rad)  
    yaw,      # Orientation around Down axis (rad)
    bias_x,   # Gyroscope bias in X direction (rad/s)
    bias_y,   # Gyroscope bias in Y direction (rad/s)
    bias_z    # Gyroscope bias in Z direction (rad/s)
]
```

## 🔄 **How EKF Works**

### **1. Prediction Step (uses gyroscope)**
```python
# Uses calibrated gyroscope rates to predict next state
predicted_orientation = current_orientation + gyro_rates * dt
predicted_biases = current_biases  # Biases change slowly
```

### **2. Update Step (uses accelerometer & magnetometer)**
```python
# Compares predictions with absolute sensor measurements
accel_measurement = gravity_vector_from_current_orientation
mag_measurement = magnetic_field_from_current_yaw

# Optimally blends prediction with measurements
optimal_estimate = weighted_combination(prediction, measurements)
```

### **3. Automatic Bias Estimation**
```python
# EKF continuously estimates and corrects gyroscope biases
estimated_bias = filter_learns_bias_over_time()
corrected_gyro = raw_gyro - estimated_bias
```

## 📊 **Data Flow Architecture**

```
Raw Sensors → Calibration → NED Transform → EKF → Optimal Orientation
     ↑             ↑              ↑           ↑           ↑
   ICM20948    Our Cal File   Our Testing   This EKF   Final Output
```

## 🎛️ **Key Features**

### **✅ Optimal Sensor Fusion**
- **Mathematically proven** best linear estimator
- **Weighted combination** based on sensor reliability
- **Adaptive** - trusts different sensors in different situations

### **✅ Automatic Bias Correction**
- **Continuously estimates** gyroscope biases
- **No manual calibration** needed for bias
- **Adapts** to changing conditions

### **✅ Robust Performance**
- **Handles sharp movements** without diverging
- **No manual resets** required
- **Graceful degradation** when sensors fail

### **✅ Uncertainty Quantification**
- **Knows how confident** it is in estimates
- **Provides uncertainty bounds** for each angle
- **Useful for control system design**

## 📱 **Usage**

### **Prerequisites:**
1. **Calibrated sensor**: Run `python3 calibrate_raw_sensors.py` first
2. **Numpy installed**: `sudo apt install python3-numpy`

### **Run the EKF:**
```bash
# On your Raspberry Pi
python3 icm20948_ekf.py
```

## 📊 **Output Display**

```
EKF ORIENTATION ESTIMATE    GYRO BIAS ESTIMATES     UNCERTAINTY
Roll  Pitch  Yaw           X     Y     Z           Roll Pitch Yaw
(°)   (°)    (°)           (°/s) (°/s) (°/s)       (°)  (°)   (°)
---------------------------------------------------------------------------
+12.3 -5.1   247.8         -0.15 +0.08 -0.22       2.1  1.8   4.5
```

### **Understanding the Output:**
- **Orientation**: Current roll, pitch, yaw estimates (degrees)
- **Bias Estimates**: Gyroscope biases being automatically corrected (°/s)
- **Uncertainty**: How confident the EKF is in each estimate (±degrees)

## 🔧 **Technical Implementation**

### **Noise Parameters (tunable)**
```python
# Initial uncertainty
P[0:3, 0:3] *= 0.1**2    # ±6° initial orientation uncertainty
P[3:6, 3:6] *= 0.01**2   # ±0.6°/s initial bias uncertainty

# Process noise (how much we trust predictions)
Q[0:3, 0:3] *= 0.001**2  # Small orientation process noise
Q[3:6, 3:6] *= 1e-6      # Very small bias process noise

# Measurement noise (how much we trust sensors)
R_accel *= 0.1**2        # ±0.1g accelerometer noise
R_mag *= 5.0**2          # ±5µT magnetometer noise
```

### **Euler Angle Kinematics**
```python
# Converts gyroscope rates to orientation changes
roll_dot = ωx + ωy*sin(φ)*tan(θ) + ωz*cos(φ)*tan(θ)
pitch_dot = ωy*cos(φ) - ωz*sin(φ)  
yaw_dot = ωy*sin(φ)/cos(θ) + ωz*cos(φ)/cos(θ)
```

### **Jacobian Computation**
```python
# Linearizes nonlinear dynamics for EKF
F = ∂f/∂x  # Process model Jacobian
H = ∂h/∂x  # Measurement model Jacobian
```

## 🧪 **Testing the EKF**

### **1. Initialization Test**
- Place sensor level → Should initialize with reasonable angles
- Watch bias estimates → Should start near zero

### **2. Sharp Movement Test**  
- Make rapid rotations → EKF should track smoothly without diverging
- Compare with manual integration → EKF should be much more stable

### **3. Bias Estimation Test**
- Let EKF run for several minutes → Bias estimates should converge
- Note final bias values → Should be small and stable

### **4. Uncertainty Test**
- Watch uncertainty values → Should decrease as EKF gains confidence
- During motion → Uncertainty should increase appropriately

## 💡 **EKF vs Manual Integration Comparison**

| Aspect | Manual Integration | Extended Kalman Filter |
|--------|-------------------|------------------------|
| **Sharp movements** | ❌ Causes large errors | ✅ Handles gracefully |
| **Bias correction** | ❌ Manual resets needed | ✅ Automatic estimation |
| **Sensor fusion** | ❌ Simple averaging | ✅ Optimal weighting |
| **Uncertainty** | ❌ Unknown accuracy | ✅ Quantified confidence |
| **Robustness** | ❌ Diverges over time | ✅ Self-correcting |
| **Maintenance** | ❌ Requires intervention | ✅ Autonomous operation |

## 🎯 **Configuration Options**

### **Magnetic Declination**
```python
self.magnetic_declination = 0.0  # Adjust for your location
```

### **Noise Tuning**
- **Increase Q**: If EKF responds too slowly to motion
- **Decrease Q**: If EKF is too noisy/jittery
- **Increase R**: If sensors are very noisy
- **Decrease R**: If sensors are very accurate

### **Update Rate**
```python
time.sleep(0.05)  # 20Hz - adjust for desired performance
```

## 🚨 **Troubleshooting**

### **EKF Diverges/Goes Unstable**
- Check calibration quality
- Verify NED transformations are correct
- Reduce process noise (Q)

### **EKF Too Slow to Respond**
- Increase process noise (Q)
- Decrease measurement noise (R)

### **Biases Don't Converge**
- Ensure enough motion for observability
- Check gyroscope calibration
- Increase bias process noise

### **High Uncertainty Values**
- Normal during startup and motion
- Should decrease when stationary
- Check sensor data quality

## 🎉 **Success Criteria**

Your EKF is working correctly when:
- ✅ **Smooth tracking** during all types of motion
- ✅ **No manual resets** needed
- ✅ **Bias estimates** converge to small stable values  
- ✅ **Uncertainty** decreases when stationary
- ✅ **Sharp movements** handled without issues
- ✅ **Long-term stability** without drift

## 🚀 **Next Steps**

With a working EKF, you can now:
1. **Integrate with control systems** - use orientation for vehicle control
2. **Log data** - record performance for analysis
3. **Tune parameters** - optimize for your specific application
4. **Add features** - position estimation, velocity estimation, etc.

## 📁 **Related Files**

- **`icm20948_ekf.py`**: The complete EKF implementation
- **`icm20948_ned_corrected.py`**: Sensor interface class
- **`icm20948_raw_calibration.json`**: Calibration parameters
- **`orientation_from_calibrated_data.py`**: Manual fusion (for comparison)

## 💫 **Congratulations!**

You've successfully implemented a **professional-grade Extended Kalman Filter** for orientation estimation! This represents the culmination of:

- ✅ **Sensor connection** and verification
- ✅ **Coordinate system** alignment  
- ✅ **Proper calibration** methodology
- ✅ **Sensor fusion** understanding
- ✅ **EKF implementation** mastery

Your ICM20948 system is now ready for **real-world applications** requiring robust, accurate, autonomous orientation estimation! 🎯🚀 