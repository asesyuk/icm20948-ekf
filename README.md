# 🎯 ICM20948 Extended Kalman Filter for Orientation Estimation

A **professional-grade Extended Kalman Filter implementation** for robust, real-time orientation estimation using the ICM20948 9-DOF IMU sensor on Raspberry Pi.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)](https://www.raspberrypi.org/)

## 🚀 **Features**

- **✅ Complete 6-DOF orientation estimation** (roll, pitch, yaw + gyroscope bias estimation)
- **✅ Automatic gyroscope bias correction** - no manual calibration needed
- **✅ Robust handling of sharp movements** - no manual resets required
- **✅ Real-time uncertainty quantification** - know how confident your estimates are
- **✅ Professional sensor calibration** methodology with abnormality detection
- **✅ NED coordinate system compliance** for aviation/robotics standards
- **✅ 20Hz real-time operation** with efficient computation
- **✅ Optimal sensor fusion** combining accelerometer, gyroscope, and magnetometer

## 📊 **What This Solves**

Traditional gyroscope integration fails during **sharp movements** and accumulates **drift over time**. This EKF implementation provides:

| Problem | Traditional Approach | This EKF Solution |
|---------|---------------------|-------------------|
| Sharp movements | ❌ Large errors, manual resets | ✅ Graceful handling |
| Gyroscope drift | ❌ Accumulates over time | ✅ Automatically corrected |
| Sensor fusion | ❌ Simple averaging | ✅ Optimal weighting |
| Uncertainty | ❌ Unknown reliability | ✅ Quantified confidence |
| Maintenance | ❌ Requires intervention | ✅ Autonomous operation |

## 🛠️ **Hardware Requirements**

- **Raspberry Pi** (3B+ or newer recommended)
- **ICM20948 9-DOF IMU** sensor breakout board
- **I2C connection** (4 wires: VCC, GND, SDA, SCL)

### **Wiring Diagram**

| ICM20948 Pin | Raspberry Pi Pin | GPIO | Notes |
|--------------|------------------|------|-------|
| VCC/VDD      | Pin 1 (3.3V)     | -    | ⚠️ Use 3.3V, NOT 5V |
| GND          | Pin 6 (GND)      | -    | |
| SDA          | Pin 3            | GPIO 2 | I2C Data |
| SCL          | Pin 5            | GPIO 3 | I2C Clock |
| AD0          | GND or 3.3V      | -    | Address select (0x68/0x69) |

## 🚀 **Quick Start**

### **1. Hardware Setup**
```bash
# Enable I2C on Raspberry Pi
sudo raspi-config
# Navigate to: Interface Options > I2C > Enable
sudo reboot
```

### **2. Install Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3-pip python3-numpy i2c-tools python3-smbus -y

# Verify I2C connection
i2cdetect -y 1
# Should show device at 0x68 or 0x69
```

### **3. Clone and Setup**
```bash
# Clone this repository
git clone https://github.com/asesyuk/icm20948-ekf.git
cd icm20948-ekf

# Make scripts executable
chmod +x *.sh *.py
```

### **4. Verify Connection**
```bash
# Test basic ICM20948 connectivity
python3 check_icm20948_connection.py
# Should show: ✓ ICM20948 found and responding!
```

### **5. Calibrate Sensors**
```bash
# IMPORTANT: Run calibration first (20-30 minutes)
python3 calibrate_raw_sensors.py

# This creates: icm20948_raw_calibration.json
# Follow on-screen prompts for sensor positioning
```

### **6. Run Extended Kalman Filter**
```bash
# Start real-time EKF orientation estimation
python3 icm20948_ekf.py

# Output: Real-time roll/pitch/yaw with bias estimates and uncertainty
```

## 📁 **Project Structure**

### **🎯 Main Implementation**
```
icm20948_ekf.py                    # Main EKF implementation (START HERE)
calibrate_raw_sensors.py           # Sensor calibration (RUN FIRST)
icm20948_ned_corrected.py          # Sensor interface with NED transforms
orientation_from_calibrated_data.py # Manual fusion comparison
```

### **📊 Configuration & Data**
```
icm20948_raw_calibration.json      # Generated calibration parameters
transfer_to_pi.sh                  # Automated file transfer script
```

### **📖 Documentation**
```
ICM20948_EKF_GUIDE.md              # Complete EKF usage guide
PROJECT_COMPLETION_SUMMARY.md      # Full project documentation
CALIBRATION_COORDINATE_SYSTEMS.md  # Calibration methodology explanation
YAW_DIRECTION_FIX.md               # NED convention compliance
GYRO_INTEGRATION_IMPROVEMENTS.md   # Integration problem solutions
```

### **🔧 Testing & Utilities**
```
check_icm20948_connection.py       # Basic connectivity test
debug_magnetometer.py              # Magnetometer diagnostics
fix_magnetometer_continuous.py     # Magnetometer setup fix
test_*_directions.py               # Sensor direction verification
```

## 🎯 **Usage Examples**

### **Basic EKF Orientation Estimation**
```python
from icm20948_ekf import ICM20948_EKF

# Initialize EKF with calibration
ekf = ICM20948_EKF("icm20948_raw_calibration.json")
ekf.initialize()

# Get orientation estimate
orientation = ekf.get_orientation_degrees()
print(f"Roll: {orientation['roll']:.1f}°")
print(f"Pitch: {orientation['pitch']:.1f}°") 
print(f"Yaw: {orientation['yaw']:.1f}°")

# Get gyroscope bias estimates
biases = ekf.get_gyro_biases_degrees()
print(f"Bias X: {biases['bias_x']:.2f}°/s")

# Get uncertainty bounds
uncertainty = ekf.get_uncertainty()
print(f"Roll uncertainty: ±{uncertainty['roll_std']:.1f}°")
```

### **Real-time Data Logging**
```bash
# Log EKF output to file
python3 icm20948_ekf.py > orientation_log.txt

# Or with timestamp
python3 icm20948_ekf.py | while read line; do 
    echo "$(date): $line" >> timestamped_log.txt
done
```

## 📊 **Expected Output**

```
🎯 ICM20948 Extended Kalman Filter
============================================================
EKF ORIENTATION ESTIMATE    GYRO BIAS ESTIMATES     UNCERTAINTY
Roll  Pitch  Yaw           X     Y     Z           Roll Pitch Yaw
(°)   (°)    (°)           (°/s) (°/s) (°/s)       (°)  (°)   (°)
---------------------------------------------------------------------------
+12.3 -5.1   247.8         -0.15 +0.08 -0.22       2.1  1.8   4.5
```

**Understanding the output:**
- **Left**: Current orientation estimates (degrees)
- **Middle**: Gyroscope biases being automatically corrected (°/s)
- **Right**: Uncertainty bounds - how confident the EKF is (±degrees)

## 🔧 **Configuration**

### **Tunable EKF Parameters** (in `icm20948_ekf.py`)
```python
# Process noise (how much to trust predictions)
self.Q[0:3, 0:3] *= 0.001**2  # Orientation process noise
self.Q[3:6, 3:6] *= 1e-6      # Bias process noise

# Measurement noise (how much to trust sensors)  
self.R_accel *= 0.1**2        # Accelerometer noise (~0.1g)
self.R_mag *= 5.0**2          # Magnetometer noise (~5µT)

# Magnetic declination (adjust for your location)
self.magnetic_declination = 0.0  # degrees
```

### **Update Rate**
```python
time.sleep(0.05)  # 20Hz (adjust as needed)
```

## 🧪 **Testing & Validation**

### **1. Sensor Connection Test**
```bash
python3 check_icm20948_connection.py
```

### **2. Individual Sensor Verification**
```bash
python3 test_corrected_ned.py           # Accelerometer
python3 test_gyro_ned_directions.py     # Gyroscope  
python3 test_magnetometer_ned_directions.py # Magnetometer
```

### **3. Calibration Quality Check**
```bash
python3 calibrate_raw_sensors.py
# Check for abnormalities in output
```

### **4. EKF vs Manual Comparison**
```bash
python3 orientation_from_calibrated_data.py
# Compare EKF with manual integration
```

## 🚨 **Troubleshooting**

### **Connection Issues**
```bash
# Check I2C devices
i2cdetect -y 1

# Verify wiring (especially 3.3V vs 5V)
# Add user to i2c group if permission denied
sudo usermod -a -G i2c $USER
```

### **Calibration Problems**
```bash
# If calibration shows abnormalities:
python3 debug_magnetometer.py           # Magnetometer issues
python3 fix_magnetometer_continuous.py  # Fix magnetometer mode
```

### **EKF Performance Issues**
- **Too slow to respond**: Increase process noise (Q)
- **Too noisy**: Decrease process noise (Q)  
- **Biases don't converge**: Ensure sufficient motion during operation
- **High uncertainty**: Normal during startup/motion, should decrease when stationary

## 🎯 **Coordinate System**

This implementation uses **NED (North-East-Down) convention**:
- **X-axis**: North (forward)
- **Y-axis**: East (right)  
- **Z-axis**: Down (toward Earth)
- **Positive rotations**: Right-hand rule around each axis

### **Sensor-Specific Transformations**
Different sensors on the ICM20948 require different coordinate transformations:

```python
# Accelerometer: [+X, +Y, -Z] → [North, East, Down]
# Gyroscope:     [-X, -Y, +Z] → [North, East, Down]
# Magnetometer:  [-X, -Y, -Z] → [North, East, Down]
```

## 📚 **Documentation**

- **[ICM20948_EKF_GUIDE.md](ICM20948_EKF_GUIDE.md)** - Complete EKF implementation guide
- **[CALIBRATION_COORDINATE_SYSTEMS.md](CALIBRATION_COORDINATE_SYSTEMS.md)** - Critical calibration methodology
- **[PROJECT_COMPLETION_SUMMARY.md](PROJECT_COMPLETION_SUMMARY.md)** - Full project journey
- **[YAW_DIRECTION_FIX.md](YAW_DIRECTION_FIX.md)** - NED convention alignment

## 🚀 **Applications**

This EKF implementation is suitable for:

- **🚁 UAV/Drone flight control** - Attitude estimation for autonomous flight
- **🚗 Autonomous vehicles** - Vehicle orientation for navigation systems  
- **🤖 Robotics** - Robot orientation for path planning and control
- **📱 AR/VR applications** - Precise motion tracking for immersive experiences
- **⚖️ Balance control** - Self-balancing vehicles and walking robots

## 🔬 **Technical Details**

### **State Vector** (6 dimensions)
```
[roll, pitch, yaw, bias_x, bias_y, bias_z]
```

### **Prediction Step**
- Uses gyroscope data with Euler angle kinematics
- Automatically accounts for estimated biases
- Propagates uncertainty through Jacobian linearization

### **Update Step**  
- Accelerometer provides absolute roll/pitch reference
- Magnetometer provides absolute yaw reference
- Optimal sensor fusion using Kalman gain

### **Key Algorithms**
- **Euler angle integration** for orientation prediction
- **Jacobian computation** for proper EKF linearization
- **Tilt-compensated magnetometer** heading calculation
- **Automatic bias estimation** for gyroscope drift correction

## 🤝 **Contributing**

Contributions welcome! Areas for enhancement:

- **Unscented Kalman Filter** implementation for better nonlinear handling
- **GPS integration** for absolute position reference
- **Additional sensors** (barometer, camera) for enhanced state estimation
- **Parameter auto-tuning** using machine learning
- **Real-time visualization** tools

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- **ICM20948 datasheet** and technical documentation
- **Extended Kalman Filter** theory and implementation references
- **NED coordinate system** standards for aviation/robotics applications
- **Raspberry Pi community** for I2C interfacing guidance

## 📞 **Support**

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Comprehensive guides included in repository
- **Examples**: Multiple test scripts and usage examples provided

---

**🎯 Ready for professional deployment in real-world orientation estimation applications!** 