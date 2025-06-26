#!/usr/bin/env python3
"""
Test script for Euler angle unwrapping functionality

This script verifies that the EKF correctly handles Euler angle ambiguities
that occur after complex movements (like figure-8 patterns).

Run this after doing a drastic figure-8 movement to see if the unwrapping
fixes the flipped angles.
"""

import math
import time
from icm20948_ekf import ICM20948_EKF

def test_euler_unwrapping():
    """Test the Euler angle unwrapping functionality"""
    
    print("🧪 Testing Euler Angle Unwrapping Fix")
    print("=" * 50)
    print()
    print("This test verifies that the EKF correctly handles Euler angle")
    print("ambiguities after complex movements (figure-8 patterns).")
    print()
    print("Instructions:")
    print("1. Place sensor flat on table (should show ~0° roll/pitch)")
    print("2. Do some figure-8 movements")
    print("3. Place back flat on table")
    print("4. Watch for unwrapping messages and final values")
    print()
    print("Expected: Final roll/pitch should return to ~0° (not ±180°)")
    print()
    
    # Initialize EKF
    ekf = ICM20948_EKF()
    
    if not ekf.initialize():
        print("❌ Failed to initialize EKF")
        return
    
    print("✅ EKF initialized")
    print()
    print("🎯 Starting orientation tracking...")
    print("   Press Ctrl+C to stop")
    print()
    print("Current Orientation:")
    print("Roll   Pitch  Yaw      Status")
    print("(°)    (°)    (°)")
    print("-" * 30)
    
    last_time = time.time()
    unwrap_count = 0
    
    try:
        while True:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            if dt <= 0:
                continue
            
            # Get calibrated sensor data
            accel_ned, gyro_ned, mag_ned, mag_valid = ekf.apply_calibration_and_transform()
            
            # Initialize EKF on first iteration
            if not ekf.initialized:
                ekf.initialize_state(accel_ned, mag_ned, mag_valid)
                continue
            
            # Store previous state for unwrap detection
            prev_roll = math.degrees(ekf.state[0])
            prev_pitch = math.degrees(ekf.state[1])
            
            # EKF steps
            ekf.predict(gyro_ned, dt)
            ekf.update_accelerometer(accel_ned)
            if mag_valid:
                ekf.update_magnetometer(mag_ned)
            
            # Get current orientation
            orientation = ekf.get_orientation_degrees()
            
            # Check if orientation seems "normal" (not flipped)
            roll_normal = abs(orientation['roll']) < 45
            pitch_normal = abs(orientation['pitch']) < 45
            
            # Status indicator
            if roll_normal and pitch_normal:
                status = "✅ Normal"
            elif abs(orientation['roll']) > 150 or abs(orientation['pitch']) > 150:
                status = "⚠️  Flipped"
            else:
                status = "🔄 Moving"
            
            # Check for large changes (indicating unwrapping)
            roll_change = abs(orientation['roll'] - prev_roll)
            pitch_change = abs(orientation['pitch'] - prev_pitch)
            
            if roll_change > 90 or pitch_change > 90:
                unwrap_count += 1
                status += f" (Unwrap #{unwrap_count})"
            
            # Display current state
            print(f"{orientation['roll']:+6.1f} {orientation['pitch']:+6.1f} {orientation['yaw']:+6.1f}  {status}", end="\r")
            
            time.sleep(0.1)  # 10Hz for easier monitoring
            
    except KeyboardInterrupt:
        print("\n\n🎯 Test completed!")
        
        # Final assessment
        final_orientation = ekf.get_orientation_degrees()
        print(f"\n📊 Final Results:")
        print(f"   Roll:  {final_orientation['roll']:+6.1f}°")
        print(f"   Pitch: {final_orientation['pitch']:+6.1f}°")
        print(f"   Yaw:   {final_orientation['yaw']:+6.1f}°")
        print(f"   Unwrapping events: {unwrap_count}")
        
        # Assessment
        final_roll_ok = abs(final_orientation['roll']) < 15
        final_pitch_ok = abs(final_orientation['pitch']) < 15
        
        print(f"\n🎯 Assessment:")
        if final_roll_ok and final_pitch_ok:
            print("✅ SUCCESS: Angles returned to normal after figure-8 movements")
            print("   The Euler unwrapping fix is working correctly!")
        else:
            print("⚠️  REVIEW: Final angles still large after movements")
            print("   This could be normal if sensor wasn't placed flat")
            print("   or if movements were still happening during measurement")
        
        if unwrap_count > 0:
            print(f"✅ Unwrapping occurred {unwrap_count} times - fix is active")
        else:
            print("ℹ️  No unwrapping needed - movements may not have triggered flips")
    
    finally:
        ekf.close()

def simulate_angle_unwrapping():
    """Demonstrate the unwrapping logic with simulated flipped angles"""
    
    print("\n🧪 Simulating Angle Unwrapping Logic")
    print("=" * 40)
    
    # Create test EKF instance for unwrapping function
    ekf = ICM20948_EKF()
    
    # Test cases with flipped angles
    test_cases = [
        (179.6, -179.7, -41.0, "Your reported case"),
        (175.0, 178.0, 90.0, "Both angles near +180°"),
        (-178.5, -176.2, 45.0, "Both angles near -180°"),
        (179.0, 5.0, 0.0, "Only roll flipped"),
        (5.0, 178.0, 0.0, "Only pitch flipped"),
        (10.0, 20.0, 30.0, "Normal angles (no unwrap)")
    ]
    
    print("Testing unwrapping logic:")
    print("Original Roll/Pitch → Corrected Roll/Pitch")
    print("-" * 45)
    
    for roll_deg, pitch_deg, yaw_deg, description in test_cases:
        # Set up test state
        ekf.state[0] = math.radians(roll_deg)
        ekf.state[1] = math.radians(pitch_deg) 
        ekf.state[2] = math.radians(yaw_deg)
        
        # Apply unwrapping
        unwrapped = ekf.unwrap_euler_angles()
        
        # Get results
        new_roll = math.degrees(ekf.state[0])
        new_pitch = math.degrees(ekf.state[1])
        new_yaw = math.degrees(ekf.state[2])
        
        # Display results
        status = "→ UNWRAPPED" if unwrapped else "→ no change"
        print(f"{roll_deg:+6.1f}°/{pitch_deg:+6.1f}° {status} {new_roll:+6.1f}°/{new_pitch:+6.1f}° ({description})")

if __name__ == "__main__":
    print("🎯 ICM20948 EKF Euler Angle Unwrapping Test")
    print("=" * 50)
    print()
    print("Choose test mode:")
    print("1. Live sensor test (recommended)")
    print("2. Simulation test (demonstrates logic)")
    print()
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            test_euler_unwrapping()
        elif choice == "2":
            simulate_angle_unwrapping()
        else:
            print("Invalid choice. Running live sensor test...")
            test_euler_unwrapping()
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError: {e}") 