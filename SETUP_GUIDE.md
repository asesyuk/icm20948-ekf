# 🚀 ICM20948 EKF Setup Guide

**Complete step-by-step setup guide for getting the Extended Kalman Filter running on your Raspberry Pi.**

## 📋 **Prerequisites Checklist**

### **Hardware Required**
- [ ] Raspberry Pi (3B+ or newer recommended)
- [ ] ICM20948 9-DOF IMU sensor breakout board
- [ ] 4 jumper wires (Female-to-Female for breadboard connections)
- [ ] Breadboard (optional but recommended)
- [ ] SD card (16GB+) with Raspberry Pi OS

### **Software Requirements**
- [ ] Raspberry Pi OS (Bullseye or newer)
- [ ] SSH access or direct Pi access
- [ ] Internet connection on Pi

## 🔌 **Hardware Setup**

### **1. Wiring Connections**
```
ICM20948 Breakout → Raspberry Pi
─────────────────────────────────
VCC/VDD    →    Pin 1  (3.3V)     ⚠️  NEVER use 5V!
GND        →    Pin 6  (GND)
SDA        →    Pin 3  (GPIO 2)
SCL        →    Pin 5  (GPIO 3)
AD0        →    GND (for 0x68) or 3.3V (for 0x69)
```

### **2. Double-Check Connections**
- **3.3V NOT 5V**: ICM20948 is NOT 5V tolerant
- **Secure connections**: Loose wires cause intermittent failures
- **Correct pins**: Double-check GPIO 2/3 for I2C

## 💻 **Software Setup**

### **Step 1: Enable I2C**
```bash
# Enable I2C interface
sudo raspi-config

# Navigate to:
# → Interface Options
# → I2C
# → Enable
# → Finish
# → Reboot? Yes

sudo reboot
```

### **Step 2: Install Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install I2C tools and Python libraries
sudo apt install -y python3-pip python3-numpy i2c-tools python3-smbus git

# Verify I2C is working
i2cdetect -y 1
# Should show a device at 0x68 or 0x69
```

### **Step 3: Clone Repository**
```bash
# Go to home directory
cd ~

# Clone the EKF repository
git clone https://github.com/asesyuk/icm20948-ekf.git

# Enter project directory
cd icm20948-ekf

# Make all scripts executable
chmod +x *.py *.sh
```

## 🧪 **Verification & Testing**

### **Step 4: Test Hardware Connection**
```bash
# Test basic I2C connectivity
python3 check_icm20948_connection.py
```

**Expected output:**
```
✓ ICM20948 found at address 0x68
✓ WHO_AM_I register matches expected value (0xEA)
✓ ICM20948 is properly connected and responding!
```

**If this fails:**
- Check wiring (especially 3.3V vs 5V)
- Verify I2C is enabled: `sudo raspi-config`
- Check device detection: `i2cdetect -y 1`

### **Step 5: Test Individual Sensors**
```bash
# Test accelerometer NED directions
python3 test_corrected_ned.py

# Test gyroscope NED directions  
python3 test_gyro_ned_directions.py

# Test magnetometer (may need fixing first)
python3 test_magnetometer_ned_directions.py
```

**If magnetometer fails:**
```bash
# Fix magnetometer continuous mode
python3 fix_magnetometer_continuous.py

# Then retry magnetometer test
python3 test_magnetometer_ned_directions.py
```

## 📊 **Sensor Calibration**

### **Step 6: Calibrate Raw Sensors (CRITICAL)**
```bash
# Run comprehensive sensor calibration
python3 calibrate_raw_sensors.py
```

**This process takes 20-30 minutes and requires:**
- **Accelerometer**: 6 positions (each face on table for 10 seconds)
- **Gyroscope**: Keep stationary for bias estimation  
- **Magnetometer**: Smooth figure-8 motions in multiple orientations

**Generated file:** `icm20948_raw_calibration.json`

**Important notes:**
- ✅ Keep calibration file - needed for EKF
- ✅ Calibration corrects sensor imperfections
- ✅ Must be done in RAW coordinates (before NED transform)
- ❌ Don't skip this step - EKF needs calibrated data

## 🎯 **Extended Kalman Filter**

### **Step 7: Run the EKF**
```bash
# Start real-time EKF orientation estimation
python3 icm20948_ekf.py
```

**Expected output:**
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
- **Left columns**: Current orientation (roll/pitch/yaw in degrees)
- **Middle columns**: Gyroscope biases being automatically corrected
- **Right columns**: Uncertainty bounds (±degrees) - confidence measure

### **Step 8: Validate Performance**
```bash
# Compare EKF vs manual integration
python3 orientation_from_calibrated_data.py

# This shows why EKF is better than simple gyro integration
```

## 🔧 **Optional Enhancements**

### **Auto-Start on Boot** (Optional)
```bash
# Edit crontab
crontab -e

# Add this line:
@reboot cd /home/pi/icm20948-ekf && python3 icm20948_ekf.py > /home/pi/ekf_log.txt 2>&1

# Save and exit
```

### **Log to File** (Optional)
```bash
# Log EKF output with timestamps
python3 icm20948_ekf.py | while read line; do 
    echo "$(date): $line" >> orientation_log.txt
done
```

### **Remote Access** (Optional)
```bash
# Stream output over network (from another machine)
ssh pi@your-pi-ip "cd icm20948-ekf && python3 icm20948_ekf.py"
```

## 🚨 **Troubleshooting**

### **I2C Issues**
```bash
# Check if I2C is enabled
lsmod | grep i2c

# Check device detection
i2cdetect -y 1

# Check permissions
groups $USER | grep i2c

# If not in i2c group:
sudo usermod -a -G i2c $USER
# Then logout and login again
```

### **Calibration Issues**
- **Abnormal values**: Check wiring, sensor may be damaged
- **Magnetometer not working**: Run `python3 fix_magnetometer_continuous.py`
- **Large biases**: Normal for cheap sensors, EKF will compensate

### **EKF Performance Issues**
- **Too slow to respond**: Increase process noise in `icm20948_ekf.py`
- **Too noisy**: Decrease process noise  
- **Large uncertainty**: Normal during motion, should decrease when stationary
- **Biases don't converge**: Ensure sufficient motion during operation

### **Python Import Errors**
```bash
# Install missing packages
sudo apt install python3-numpy python3-smbus

# If still having issues:
pip3 install numpy
```

## 📁 **File Transfer Scripts**

### **From Mac/Linux to Pi**
```bash
# Make transfer script executable
chmod +x transfer_to_pi.sh

# Edit the script with your Pi's IP
nano transfer_to_pi.sh

# Run transfer
./transfer_to_pi.sh
```

### **Manual Transfer**
```bash
# Copy individual files
scp *.py pi@your-pi-ip:~/icm20948-ekf/

# Copy documentation
scp *.md pi@your-pi-ip:~/icm20948-ekf/
```

## ✅ **Success Criteria**

Your setup is successful when:

1. **✅ I2C Detection**: `i2cdetect -y 1` shows device at 0x68 or 0x69
2. **✅ Connection Test**: `check_icm20948_connection.py` passes
3. **✅ Sensor Tests**: All individual sensor direction tests work
4. **✅ Calibration**: `calibrate_raw_sensors.py` completes without errors
5. **✅ EKF Running**: `icm20948_ekf.py` shows stable orientation estimates
6. **✅ Low Uncertainty**: Uncertainty values decrease when stationary

## 🎯 **Next Steps**

Once your EKF is running successfully:

- **Integrate with your application**: Use the orientation data in your project
- **Tune parameters**: Adjust noise values for your specific use case
- **Add logging**: Record data for analysis
- **Mount permanently**: Secure sensor in final orientation
- **Consider GPS**: Add absolute position reference for full navigation

## 📚 **Additional Documentation**

- **[ICM20948_EKF_GUIDE.md](ICM20948_EKF_GUIDE.md)** - Complete EKF usage guide
- **[CALIBRATION_COORDINATE_SYSTEMS.md](CALIBRATION_COORDINATE_SYSTEMS.md)** - Why calibration order matters
- **[PROJECT_COMPLETION_SUMMARY.md](PROJECT_COMPLETION_SUMMARY.md)** - Full project journey

---

**🎯 Your ICM20948 EKF system is now ready for professional orientation estimation!** 