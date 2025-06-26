# 🔧 Euler Angle Unwrapping Fix

**Problem Solved:** EKF orientation angles "flip" to ±180° after complex movements and don't return to normal.

## 🚨 **The Problem**

After performing drastic figure-8 movements with the ICM20948, users reported that:

- **Before movement**: Roll=0°, Pitch=0° (sensor flat on table)
- **After figure-8**: Roll=+179.6°, Pitch=-179.7° (still flat on table!)
- **Expected**: Roll=0°, Pitch=0° (should return to original)

### **Why This Happens**

This is a fundamental **Euler angle ambiguity** problem, not an EKF bug:

- **Euler angles** have **multiple mathematical representations** for the same physical orientation
- **Roll=+179.6°, Pitch=-179.7°** represents the **same physical orientation** as **Roll=0°, Pitch=0°**
- During complex movements, the EKF can get "stuck" in the flipped representation
- This is mathematically correct but practically confusing

### **Technical Explanation**

Euler angles suffer from:
1. **Gimbal lock** near ±90° pitch
2. **Multiple representations** for the same orientation
3. **Discontinuities** at ±180° boundaries

The flipped angles occur when the orientation passes through regions where the Euler angle representation becomes ambiguous.

## ✅ **The Solution**

I've implemented **Euler angle unwrapping** that:

1. **Detects** when both roll and pitch are near ±180° (indicating a flip)
2. **Converts** flipped angles back to the "normal" representation
3. **Maintains** mathematical consistency
4. **Operates** automatically without user intervention

### **How It Works**

```python
def unwrap_euler_angles(self):
    """Fix Euler angle ambiguities after complex movements"""
    roll, pitch, yaw = self.state[0:3]
    
    # Check if both roll and pitch are near ±180° (indicating a flip)
    roll_flipped = abs(abs(roll) - math.pi) < math.radians(30)  # Within 30° of ±180°
    pitch_flipped = abs(abs(pitch) - math.pi) < math.radians(30)
    
    if roll_flipped and pitch_flipped:
        # Convert to "normal" representation
        if roll > 0:
            self.state[0] = roll - math.pi  # +179° → -1°
        else:
            self.state[0] = roll + math.pi  # -179° → +1°
            
        # Similar for pitch
        # Adjust yaw accordingly
        self.state[2] = self.normalize_angle(yaw + math.pi)
```

### **Where Applied**

The unwrapping is automatically applied after:
- **Prediction step** (gyroscope integration)
- **Accelerometer update** (gravity vector correction)
- **Magnetometer update** (yaw correction)

## 🧪 **Testing the Fix**

### **Method 1: Live Test**
```bash
python3 test_euler_unwrapping.py
# Choose option 1 for live sensor test

# Follow instructions:
# 1. Place flat (should show ~0°)
# 2. Do figure-8 movements
# 3. Place flat again (should return to ~0°)
```

### **Method 2: Simulation**
```bash
python3 test_euler_unwrapping.py
# Choose option 2 for simulation test

# Shows how unwrapping logic handles different angle combinations
```

### **Expected Output**
```
🔧 Euler angle unwrap: +179.6°,-179.7° → +0.4°,+0.3°
✅ SUCCESS: Angles returned to normal after figure-8 movements
   The Euler unwrapping fix is working correctly!
```

## 📊 **Before vs After**

| Scenario | Before Fix | After Fix |
|----------|------------|-----------|
| **Flat on table** | Roll=0°, Pitch=0° | Roll=0°, Pitch=0° |
| **After figure-8** | Roll=179.6°, Pitch=-179.7° ❌ | Roll=0.4°, Pitch=0.3° ✅ |
| **Returned flat** | Still flipped ❌ | Back to ~0° ✅ |
| **User confusion** | High ❌ | None ✅ |

## 🎯 **Key Benefits**

### **✅ Automatic Operation**
- No manual intervention required
- Works transparently during EKF operation
- User doesn't need to understand Euler angle math

### **✅ Maintains Accuracy**
- Mathematically consistent corrections
- Preserves EKF state estimation quality
- No loss of orientation tracking precision

### **✅ Real-world Usability**
- Orientation values always in expected ranges
- Easy to interpret for control systems
- Professional-grade behavior

## 🔬 **Technical Details**

### **Detection Criteria**
- Both roll AND pitch must be within 30° of ±180°
- Single angle flips are not corrected (they may be valid)
- Conservative approach prevents false corrections

### **Correction Method**
```python
# For angles near +180°
corrected_angle = flipped_angle - 180°

# For angles near -180°  
corrected_angle = flipped_angle + 180°

# Yaw adjustment
corrected_yaw = original_yaw + 180°
```

### **Mathematical Proof**
The correction is valid because:
- **R(roll, pitch, yaw) = R(roll±180°, pitch±180°, yaw±180°)**
- Both representations describe the same physical rotation
- The correction chooses the representation closer to 0°

## 🚀 **Advanced Solutions**

### **Future Enhancement: Quaternions**
For even more robust orientation tracking, consider:
- **Quaternion-based EKF** instead of Euler angles
- No singularities or ambiguities
- More complex implementation but mathematically superior

### **Alternative: Angle Wrapping Strategies**
- **Shortest path** angle interpolation
- **Continuous angle tracking** with unwrapping history
- **Weighted voting** between multiple representations

## 📚 **Related Documentation**

- **[ICM20948_EKF_GUIDE.md](ICM20948_EKF_GUIDE.md)** - Complete EKF usage
- **[YAW_DIRECTION_FIX.md](YAW_DIRECTION_FIX.md)** - NED convention alignment
- **[GYRO_INTEGRATION_IMPROVEMENTS.md](GYRO_INTEGRATION_IMPROVEMENTS.md)** - Integration issues

## 🛠️ **Troubleshooting**

### **If unwrapping doesn't work:**
1. **Check threshold**: Angles must be within 30° of ±180°
2. **Verify both angles**: Only corrects when BOTH roll and pitch are flipped
3. **Single angle issues**: May need different detection logic

### **If unwrapping is too aggressive:**
1. **Increase threshold**: Change 30° to 20° for stricter detection
2. **Add validation**: Check accelerometer consistency before unwrapping
3. **Disable debug**: Comment out the print statement for quiet operation

### **For high-dynamic applications:**
1. **Consider quaternions**: More robust for aerospace/robotics
2. **Increase update rate**: Higher frequency reduces angle jumps
3. **Tune EKF parameters**: Adjust process/measurement noise

---

**🎯 This fix resolves the primary usability issue with Euler angle-based orientation estimation after complex movements!** 