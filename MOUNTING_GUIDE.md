# ICM20948 Physical Mounting Guide for NED Compliance

## 🎯 Based on Your Current Setup

From your photo, I can see your ICM20948 is mounted with:
- ✅ Text readable from above
- ✅ Secure mounting in an enclosure
- ✅ Clean wiring setup

## 📐 Current Sensor Axes (Datasheet Standard)

**Your sensor orientation:**
```
        +Y (Forward in datasheet)
           ↑
           │
           │
+X ←───────┼───────→ -X
(Right)    │      (Left)
           │
           ↓
        -Y (Backward)

+Z points UP (away from chip surface)
-Z points DOWN (into chip surface)
```

## 🧭 NED Requirements for EKF

**NED (North-East-Down) needs:**
- **North**: Forward direction of your vehicle/platform
- **East**: Right direction of your vehicle/platform  
- **Down**: Toward Earth (positive when pointing down)

## 🔧 Mounting Options

### **Option 1: Optimal Physical Orientation**

**Recommended mounting for simplest NED compliance:**

```
Your Vehicle/Platform Layout:
┌─────────────────────────────────┐
│  FORWARD (Vehicle travels →)   │
│           ↑                     │
│           │ Mount sensor        │
│           │ so +Y points        │
│           │ this direction      │
│     ┌─────┼─────┐               │
│     │  +Y │     │               │
│ LEFT│ +X◄─┼─►-X │ RIGHT         │
│     │  -Y │     │               │
│     └─────┼─────┘               │
│           │ ICM20948            │
│           ↓                     │
│  BACKWARD                       │
└─────────────────────────────────┘
```

**This orientation gives you:**
```python
# Correct NED transformation (X=North, Y=East, Z=Down)
X_ned = +Y_sensor  # FORWARD → North (X-axis in NED)
Y_ned = +X_sensor  # RIGHT → East (Y-axis in NED)
Z_ned = -Z_sensor  # UP → Down (Z-axis in NED, negated)
```

### **Option 2: Current Mounting Analysis**

**If you cannot reorient physically:**

1. **Determine your vehicle's FORWARD direction** relative to the sensor board
2. **Determine your vehicle's RIGHT direction** relative to the sensor board
3. **Apply appropriate transformation**

**Use the orientation guidance tool:**
```bash
python3 orientation_guidance.py
```

## 🛠️ Physical Mounting Considerations

### **Vibration & Stability:**
- ✅ Your foam padding is good for vibration dampening
- ✅ Secure mounting prevents sensor movement
- ✅ Consider additional isolation if in high-vibration environment

### **Thermal Considerations:**
- ✅ ICM20948 has good temperature stability
- ✅ Avoid mounting near heat sources
- ✅ Enclosure provides thermal protection

### **Electromagnetic Interference:**
- ✅ Keep away from power electronics
- ✅ Twisted pair wiring for I2C (if long runs)
- ✅ Proper grounding

## 📊 Common Vehicle Orientations

### **Ground Vehicle (Car/Robot):**
```
Recommended sensor mounting:
+Y_sensor → Vehicle FORWARD (becomes X_ned=North)
+X_sensor → Vehicle RIGHT (becomes Y_ned=East)
+Z_sensor → UP (becomes Z_ned=Down via negation)
```

### **Marine Vessel:**
```
Recommended sensor mounting:
+Y_sensor → Bow (forward, becomes X_ned=North)
+X_sensor → Starboard (right, becomes Y_ned=East)
+Z_sensor → UP (becomes Z_ned=Down via negation)
```

### **Aircraft:**
```
Recommended sensor mounting:
+Y_sensor → Nose (forward, becomes X_ned=North)
+X_sensor → Right wing (becomes Y_ned=East)
+Z_sensor → UP (becomes Z_ned=Down via negation)
```

## 🧪 Verification Tests

### **After mounting, verify with:**

1. **Level test**: Z_ned should read ~+1g when level
2. **Forward tilt**: X_ned should be positive when tilting forward
3. **Right tilt**: Y_ned should be positive when tilting right
4. **Rotation test**: Gyro values should match rotation direction

### **Run verification:**
```bash
python3 icm20948_ned_sensor.py
```

## ⚠️ Important Notes

### **Axis Orientation:**
- **Never** physically rotate the chip on the breakout board
- **Always** consider the whole breakout board orientation
- **Remember** the text readability indicates standard orientation

### **Software vs Hardware:**
- **Physical orientation change** = simpler software
- **Software transformation** = more complex but flexible
- **Mixed approach** = sometimes necessary

### **EKF Implications:**
- Consistent coordinate system is **critical** for EKF
- Wrong orientation = incorrect attitude estimation
- NED compliance ensures compatibility with standard algorithms

## 🎯 Recommendation for Your Setup

Based on your photo:

1. **Determine** which direction your vehicle/platform moves forward
2. **Check** if that aligns with the +Y direction of your sensor board
3. **If yes**: Use simple transformation (X_ned=+Y_sensor, Y_ned=+X_sensor, Z_ned=-Z_sensor)
4. **If no**: Use the orientation guidance tool to determine correct transformation
5. **Test** thoroughly with live data before EKF implementation

Your mounting looks solid and professional - the key is just ensuring the coordinate transformation is correct for your vehicle's reference frame! 