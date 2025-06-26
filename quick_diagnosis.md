# Quick ICM20948 Diagnosis - "Error: Read failed"

You're getting "Error: Read failed" when running `i2cget -y 1 0x68 0x00`. Here's what to check immediately:

## Step 1: Check if any I2C devices are detected
```bash
i2cdetect -y 1
```

**Expected output if working:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --
```

**If you see all "--" (no devices):**
- ICM20948 is not connected or not responding
- Check wiring, especially power and ground

**If you see a device at 0x69 instead of 0x68:**
- Try: `i2cget -y 1 0x69 0x00`
- Your AD0 pin might be connected to 3.3V instead of GND

## Step 2: Check different I2C bus
Some Raspberry Pi configurations use bus 0:
```bash
i2cdetect -y 0
```

If devices appear on bus 0, use that instead:
```bash
i2cget -y 0 0x68 0x00
```

## Step 3: Check I2C is enabled
```bash
# Check if I2C modules are loaded
lsmod | grep i2c

# Check I2C device files exist
ls -la /dev/i2c*
```

If missing, enable I2C:
```bash
sudo raspi-config
# Navigate to: Interface Options > I2C > Enable
sudo reboot
```

## Step 4: Check permissions
```bash
# Check if you're in i2c group
groups | grep i2c

# If not, add yourself:
sudo usermod -a -G i2c $USER
# Then log out and back in
```

## Step 5: Double-check wiring
Most common issues:
- **Wrong voltage**: Use 3.3V, NOT 5V (will damage ICM20948)
- **Loose connections**: Especially on breadboards
- **Swapped SDA/SCL**: SDA→GPIO2, SCL→GPIO3
- **No ground connection**: Ensure GND is connected

## Step 6: Test with the troubleshooting script
Run the comprehensive diagnostic:
```bash
python3 troubleshoot_icm20948.py
```

## Quick Fixes to Try:

1. **Try the other address:**
   ```bash
   i2cget -y 1 0x69 0x00
   ```

2. **Try bus 0:**
   ```bash
   i2cget -y 0 0x68 0x00
   ```

3. **Check if ANY devices are on the bus:**
   ```bash
   i2cdetect -y 1
   i2cdetect -y 0
   ```

4. **Verify I2C is working with a scan:**
   ```bash
   sudo i2cdetect -y 1
   ```

## Most Likely Causes:
1. **Wrong I2C address** - Try 0x69 instead of 0x68
2. **Wiring issue** - Double-check all connections
3. **I2C not enabled** - Run `sudo raspi-config`
4. **Wrong bus** - Try bus 0 instead of bus 1
5. **Power issue** - Ensure 3.3V (not 5V) and good ground

Let me know what `i2cdetect -y 1` shows! 