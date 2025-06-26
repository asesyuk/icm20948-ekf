# ICM20948 Datasheet Orientation vs NED Coordinate System

## Official ICM20948 Orientation (from datasheet)

According to the InvenSense ICM20948 datasheet Figure 12:

```
         +Y (Forward)
            ↑
            |
            |
    +X ←----+----→ -X
  (Right)   |   (Left)
            |
            ↓
         -Y (Backward)

    +Z points UP (away from chip surface)
    -Z points DOWN (into chip surface)
```

### Datasheet Coordinate System:
- **+X**: Points RIGHT (East direction)
- **+Y**: Points FORWARD (North direction)
- **+Z**: Points UP (away from chip surface)

## Your Physical Sensor Setup

You mentioned:
- **X**: Points LEFT on your sensor
- **Y**: Points FORWARD on your sensor
- **Z**: Direction unknown

## Discrepancy Analysis

### Possible Explanations:
1. **Sensor Rotation**: Your sensor is physically rotated 180° around the Z-axis
2. **Different Reference**: You're looking at the sensor from the opposite side
3. **PCB Layout**: Your breakout board has the chip oriented differently

## NED (North-East-Down) Requirements

For proper NED compliance:
- **North**: FORWARD (+Y in NED)
- **East**: RIGHT (+X in NED)
- **Down**: TOWARD EARTH (+Z in NED)

## Determining Your Transformations

### Step 1: Run the NED Orientation Test
```bash
python3 ned_orientation_test.py
```

This will:
1. Compare your readings with datasheet expectations
2. Determine exact coordinate transformations needed
3. Provide the conversion formulas for NED compliance

### Step 2: Expected Transformation Results

Based on your description (X=LEFT, Y=FORWARD), you'll likely need:

```python
# Probable transformations for NED compliance:
X_ned = -X_sensor  # Your LEFT → Need East (negate to get RIGHT)
Y_ned = +Y_sensor  # Your FORWARD → Already North (no change)
Z_ned = ?         # Depends on chip orientation (test will determine)
```

### Step 3: Apply Transformations

Once determined, apply these transformations to ALL sensor data:
- Accelerometer readings
- Gyroscope readings  
- Magnetometer readings

## Example Implementation

```python
def transform_to_ned(sensor_x, sensor_y, sensor_z):
    """Transform sensor data to NED coordinates"""
    # Replace with your determined transformations
    ned_x = -sensor_x  # LEFT → East (negate)
    ned_y = +sensor_y  # FORWARD → North (keep)
    ned_z = -sensor_z  # UP → Down (negate, if Z points up)
    
    return ned_x, ned_y, ned_z

# Apply to accelerometer
accel_ned = transform_to_ned(accel_x, accel_y, accel_z)

# Apply to gyroscope  
gyro_ned = transform_to_ned(gyro_x, gyro_y, gyro_z)

# Apply to magnetometer
mag_ned = transform_to_ned(mag_x, mag_y, mag_z)
```

## Why This Matters

### For Sensor Fusion:
- Extended Kalman Filters expect consistent coordinate systems
- Navigation algorithms assume NED compliance
- Attitude estimation requires proper axis alignment

### For Integration:
- GPS data is typically in NED coordinates
- Flight controllers expect NED inputs
- Standard algorithms are designed for NED

## Verification

After applying transformations, verify NED compliance:

1. **Stationary on flat surface**: 
   - `accel_ned = (0, 0, +1g)` ✓

2. **Facing North**:
   - `mag_ned` should have largest component on X-axis

3. **Rotating clockwise (viewed from above)**:
   - `gyro_ned_z` should be positive

## Next Steps

1. ✅ Run `ned_orientation_test.py` to determine transformations
2. ✅ Implement the transformations in your code
3. ✅ Verify NED compliance with test movements
4. ✅ Proceed with sensor fusion implementation

The test will give you the exact formulas needed for your specific sensor orientation! 