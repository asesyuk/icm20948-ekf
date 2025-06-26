#!/bin/bash
# ICM20948 I2C Connection Check Commands
# Run these commands on your Raspberry Pi

echo "ICM20948 I2C Connection Check"
echo "============================="

# Check if I2C is enabled
echo "1. Checking if I2C is enabled..."
if lsmod | grep -q i2c_bcm2708; then
    echo "✓ I2C module is loaded"
else
    echo "✗ I2C module not loaded - enable with: sudo raspi-config"
fi

# Check if I2C tools are installed
echo "2. Checking if I2C tools are installed..."
if command -v i2cdetect &> /dev/null; then
    echo "✓ i2c-tools are installed"
else
    echo "✗ i2c-tools not found - install with: sudo apt-get install i2c-tools"
    exit 1
fi

# Scan I2C bus
echo "3. Scanning I2C bus 1 for devices..."
echo "Expected ICM20948 addresses: 0x69 (AD0=HIGH) or 0x68 (AD0=LOW)"
i2cdetect -y 1

# Test specific ICM20948 addresses
echo "4. Testing ICM20948 specific addresses..."
for addr in 0x69 0x68; do
    echo -n "Testing address $addr: "
    if i2cget -y 1 $addr 0x00 &> /dev/null; then
        who_am_i=$(i2cget -y 1 $addr 0x00)
        echo "WHO_AM_I = $who_am_i (expected: 0xea)"
        if [ "$who_am_i" = "0xea" ]; then
            echo "✓ ICM20948 found and verified at address $addr"
        else
            echo "✗ Device found but WHO_AM_I doesn't match ICM20948"
        fi
    else
        echo "✗ No device responding"
    fi
done

echo ""
echo "If no devices found:"
echo "- Check wiring: VCC->3.3V, GND->GND, SDA->GPIO2, SCL->GPIO3"
echo "- Enable I2C: sudo raspi-config > Interface Options > I2C"
echo "- Reboot after enabling I2C" 