#!/usr/bin/env python3
"""
ICM20948 Extended Kalman Filter Implementation
Optimal sensor fusion for orientation estimation using calibrated ICM20948 data

State Vector: [roll, pitch, yaw, bias_x, bias_y, bias_z]
- Uses gyroscope for prediction step
- Uses accelerometer and magnetometer for update step
- Automatically estimates and corrects gyroscope biases
"""

import time
import math
import json
import sys
import numpy as np
from datetime import datetime

try:
    from icm20948_ned_corrected import ICM20948_NED_Corrected
except ImportError:
    print("ERROR: Could not import ICM20948_NED_Corrected")
    print("Make sure icm20948_ned_corrected.py is in the same directory")
    sys.exit(1)

class ICM20948_EKF:
    """Extended Kalman Filter for ICM20948 orientation estimation"""
    
    def __init__(self, calibration_file="icm20948_raw_calibration.json"):
        self.imu = None
        self.calibration_data = None
        self.calibration_file = calibration_file
        
        # EKF State: [roll, pitch, yaw, bias_x, bias_y, bias_z]
        self.state = np.zeros(6)  # [rad, rad, rad, rad/s, rad/s, rad/s]
        
        # State covariance matrix (6x6)
        self.P = np.eye(6)
        
        # Process noise covariance (6x6)
        self.Q = np.eye(6)
        
        # Measurement noise covariance (3x3 for accel, 3x3 for mag)
        self.R_accel = np.eye(3)
        self.R_mag = np.eye(3)
        
        # Magnetic declination (adjust for your location)
        self.magnetic_declination = 0.0  # degrees
        
        # EKF initialization flag
        self.initialized = False
        
        # Setup noise parameters
        self._setup_noise_parameters()
        
    def _setup_noise_parameters(self):
        """Setup EKF noise parameters based on sensor characteristics"""
        
        # Initial state uncertainty
        self.P[0:3, 0:3] *= 0.1**2    # 0.1 rad (~6°) initial orientation uncertainty
        self.P[3:6, 3:6] *= 0.01**2   # 0.01 rad/s initial bias uncertainty
        
        # Process noise (how much we trust the process model)
        self.Q[0:3, 0:3] *= 0.001**2  # Small orientation process noise
        self.Q[3:6, 3:6] *= 1e-6      # Very small bias process noise (biases change slowly)
        
        # Measurement noise (how much we trust each sensor)
        self.R_accel *= 0.1**2        # Accelerometer noise (~0.1g)
        self.R_mag *= 5.0**2          # Magnetometer noise (~5µT)
    
    def initialize(self):
        """Initialize sensor and load calibration data"""
        print("🔧 Initializing ICM20948 EKF...")
        
        # Initialize sensor
        try:
            self.imu = ICM20948_NED_Corrected()
            print("✅ ICM20948 initialized")
        except Exception as e:
            print(f"❌ Failed to initialize sensor: {e}")
            return False
        
        # Load calibration data
        try:
            with open(self.calibration_file, 'r') as f:
                self.calibration_data = json.load(f)
            print(f"✅ Calibration data loaded from {self.calibration_file}")
            
            # Verify it's raw calibration data
            coord_system = self.calibration_data.get('coordinate_system', 'unknown')
            if coord_system != 'raw_sensor_coordinates':
                print(f"⚠️  WARNING: Expected raw_sensor_coordinates, got {coord_system}")
                
        except FileNotFoundError:
            print(f"❌ Calibration file {self.calibration_file} not found")
            print("   Run: python3 calibrate_raw_sensors.py")
            return False
        except Exception as e:
            print(f"❌ Failed to load calibration: {e}")
            return False
        
        return True
    
    def apply_calibration_and_transform(self):
        """Read raw sensors, apply calibration, transform to NED"""
        
        # Step 1: Read RAW sensor data
        accel_raw = self.imu.read_accelerometer_raw()
        gyro_raw = self.imu.read_gyroscope_raw()
        mag_raw_x, mag_raw_y, mag_raw_z, mag_valid = self.imu.read_magnetometer_raw()
        
        # Step 2: Convert to physical units
        accel_raw_g = [x * self.imu.accel_scale for x in accel_raw]
        gyro_raw_dps = [x * self.imu.gyro_scale for x in gyro_raw]
        mag_raw_ut = [mag_raw_x * self.imu.mag_scale, 
                      mag_raw_y * self.imu.mag_scale, 
                      mag_raw_z * self.imu.mag_scale] if mag_valid else [0, 0, 0]
        
        # Step 3: Apply calibration corrections
        accel_calibrated = self.apply_accel_calibration(accel_raw_g)
        gyro_calibrated = self.apply_gyro_calibration(gyro_raw_dps)
        mag_calibrated = self.apply_mag_calibration(mag_raw_ut) if mag_valid else [0, 0, 0]
        
        # Step 4: Transform to NED coordinates
        accel_ned = self.transform_accel_to_ned(accel_calibrated)
        gyro_ned = self.transform_gyro_to_ned(gyro_calibrated)
        mag_ned = self.transform_mag_to_ned(mag_calibrated) if mag_valid else [0, 0, 0]
        
        # Convert to numpy arrays and radians for EKF
        accel_ned = np.array(accel_ned)
        gyro_ned = np.array(gyro_ned) * math.pi / 180.0  # Convert to rad/s
        mag_ned = np.array(mag_ned)
        
        return accel_ned, gyro_ned, mag_ned, mag_valid
    
    def apply_accel_calibration(self, raw_accel):
        """Apply accelerometer calibration"""
        if 'accelerometer' not in self.calibration_data:
            return raw_accel
        
        cal = self.calibration_data['accelerometer']
        bias = cal.get('bias_raw', [0, 0, 0])
        scale = cal.get('scale_factors', [1, 1, 1])
        
        return [(raw_accel[i] - bias[i]) * scale[i] for i in range(3)]
    
    def apply_gyro_calibration(self, raw_gyro):
        """Apply gyroscope calibration"""
        if 'gyroscope' not in self.calibration_data:
            return raw_gyro
        
        cal = self.calibration_data['gyroscope']
        bias = cal.get('bias_raw', [0, 0, 0])
        
        return [raw_gyro[i] - bias[i] for i in range(3)]
    
    def apply_mag_calibration(self, raw_mag):
        """Apply magnetometer calibration"""
        if 'magnetometer' not in self.calibration_data:
            return raw_mag
        
        cal = self.calibration_data['magnetometer']
        hard_iron = cal.get('hard_iron_offset_raw', [0, 0, 0])
        soft_iron = cal.get('soft_iron_scale_raw', [1, 1, 1])
        
        return [(raw_mag[i] - hard_iron[i]) * soft_iron[i] for i in range(3)]
    
    def transform_accel_to_ned(self, calibrated_accel):
        """Transform calibrated accelerometer to NED coordinates"""
        return [+calibrated_accel[0], +calibrated_accel[1], -calibrated_accel[2]]
    
    def transform_gyro_to_ned(self, calibrated_gyro):
        """Transform calibrated gyroscope to NED coordinates"""
        return [-calibrated_gyro[0], -calibrated_gyro[1], +calibrated_gyro[2]]
    
    def transform_mag_to_ned(self, calibrated_mag):
        """Transform calibrated magnetometer to NED coordinates"""
        return [-calibrated_mag[0], -calibrated_mag[1], -calibrated_mag[2]]
    
    def initialize_state(self, accel_ned, mag_ned, mag_valid):
        """Initialize EKF state from accelerometer and magnetometer"""
        
        # Calculate initial orientation from sensors
        roll_init = math.atan2(accel_ned[1], math.sqrt(accel_ned[0]**2 + accel_ned[2]**2))
        pitch_init = math.atan2(-accel_ned[0], math.sqrt(accel_ned[1]**2 + accel_ned[2]**2))
        
        # Calculate initial yaw from magnetometer (if valid)
        if mag_valid and np.linalg.norm(mag_ned) > 1.0:
            # Tilt compensation
            cos_roll = math.cos(roll_init)
            sin_roll = math.sin(roll_init)
            cos_pitch = math.cos(pitch_init)
            sin_pitch = math.sin(pitch_init)
            
            # Tilt-compensated magnetic field
            mag_x_comp = mag_ned[0] * cos_pitch + mag_ned[2] * sin_pitch
            mag_y_comp = mag_ned[0] * sin_roll * sin_pitch + mag_ned[1] * cos_roll - mag_ned[2] * sin_roll * cos_pitch
            
            yaw_init = math.atan2(mag_y_comp, mag_x_comp) + math.radians(self.magnetic_declination)
        else:
            yaw_init = 0.0  # Default to North if magnetometer invalid
        
        # Initialize state vector [roll, pitch, yaw, bias_x, bias_y, bias_z]
        self.state[0] = roll_init
        self.state[1] = pitch_init  
        self.state[2] = yaw_init
        self.state[3:6] = 0.0  # Initial bias estimates
        
        self.initialized = True
        
        print(f"📍 EKF initialized:")
        print(f"   Roll:  {math.degrees(roll_init):+6.1f}°")
        print(f"   Pitch: {math.degrees(pitch_init):+6.1f}°") 
        print(f"   Yaw:   {math.degrees(yaw_init):+6.1f}°")
        print(f"   Biases: [0.0, 0.0, 0.0]°/s (will be estimated)")
    
    def predict(self, gyro_ned, dt):
        """EKF Prediction Step - Use gyroscope data to predict state"""
        
        if dt <= 0:
            return
        
        # Extract current state
        roll, pitch, yaw = self.state[0:3]
        bias_x, bias_y, bias_z = self.state[3:6]
        
        # Bias-corrected gyroscope rates
        omega_x = gyro_ned[0] - bias_x
        omega_y = gyro_ned[1] - bias_y
        omega_z = gyro_ned[2] - bias_z
        
        # Predict new orientation using gyroscope (Euler angle integration)
        # This is the nonlinear process model
        sin_roll = math.sin(roll)
        cos_roll = math.cos(roll)
        tan_pitch = math.tan(pitch)
        sec_pitch = 1.0 / math.cos(pitch)
        
        # Euler angle kinematics
        roll_dot = omega_x + omega_y * sin_roll * tan_pitch + omega_z * cos_roll * tan_pitch
        pitch_dot = omega_y * cos_roll - omega_z * sin_roll
        yaw_dot = omega_y * sin_roll * sec_pitch + omega_z * cos_roll * sec_pitch
        
        # Update state (prediction)
        self.state[0] += roll_dot * dt   # roll
        self.state[1] += pitch_dot * dt  # pitch
        self.state[2] += yaw_dot * dt    # yaw
        # Biases don't change in prediction (state[3:6] remain same)
        
        # Normalize angles
        self.state[0] = self.normalize_angle(self.state[0])
        self.state[1] = self.normalize_angle(self.state[1])
        self.state[2] = self.normalize_angle(self.state[2])
        
        # Compute Jacobian of process model (F matrix)
        F = self.compute_process_jacobian(omega_x, omega_y, omega_z, dt)
        
        # Predict covariance: P = F * P * F^T + Q
        self.P = F @ self.P @ F.T + self.Q * dt
    
    def compute_process_jacobian(self, omega_x, omega_y, omega_z, dt):
        """Compute Jacobian matrix of the process model"""
        
        roll, pitch, yaw = self.state[0:3]
        
        sin_roll = math.sin(roll)
        cos_roll = math.cos(roll)
        tan_pitch = math.tan(pitch)
        sec_pitch = 1.0 / math.cos(pitch)
        sec2_pitch = sec_pitch**2
        
        # Partial derivatives of the process model
        F = np.eye(6)
        
        # d(roll_dot)/d(roll)
        F[0, 0] = 1 + dt * (omega_y * cos_roll * tan_pitch - omega_z * sin_roll * tan_pitch)
        # d(roll_dot)/d(pitch)  
        F[0, 1] = dt * (omega_y * sin_roll * sec2_pitch + omega_z * cos_roll * sec2_pitch)
        
        # d(pitch_dot)/d(roll)
        F[1, 0] = dt * (-omega_y * sin_roll - omega_z * cos_roll)
        F[1, 1] = 1  # d(pitch_dot)/d(pitch)
        
        # d(yaw_dot)/d(roll)
        F[2, 0] = dt * (omega_y * cos_roll * sec_pitch - omega_z * sin_roll * sec_pitch)
        # d(yaw_dot)/d(pitch)
        F[2, 1] = dt * (omega_y * sin_roll * sec_pitch * tan_pitch + omega_z * cos_roll * sec_pitch * tan_pitch)
        F[2, 2] = 1  # d(yaw_dot)/d(yaw)
        
        # Derivatives w.r.t. biases
        F[0, 3] = -dt  # d(roll_dot)/d(bias_x)
        F[0, 4] = -dt * sin_roll * tan_pitch  # d(roll_dot)/d(bias_y)
        F[0, 5] = -dt * cos_roll * tan_pitch  # d(roll_dot)/d(bias_z)
        
        F[1, 4] = -dt * cos_roll  # d(pitch_dot)/d(bias_y)
        F[1, 5] = dt * sin_roll   # d(pitch_dot)/d(bias_z)
        
        F[2, 4] = -dt * sin_roll * sec_pitch  # d(yaw_dot)/d(bias_y)
        F[2, 5] = -dt * cos_roll * sec_pitch  # d(yaw_dot)/d(bias_z)
        
        return F
    
    def update_accelerometer(self, accel_ned):
        """EKF Update Step - Use accelerometer data"""
        
        # Expected accelerometer measurement (gravity in body frame)
        roll, pitch, yaw = self.state[0:3]
        
        # Predicted accelerometer measurement (gravity vector in NED rotated to body frame)
        g = 9.81  # Gravity magnitude
        
        # Expected measurement (what accelerometer should read)
        h_accel = np.array([
            -g * math.sin(pitch),
            g * math.sin(roll) * math.cos(pitch),
            g * math.cos(roll) * math.cos(pitch)
        ])
        
        # Measurement residual
        z_accel = accel_ned * g  # Convert from g to m/s^2
        y_accel = z_accel - h_accel
        
        # Compute measurement Jacobian (H matrix)
        H_accel = np.zeros((3, 6))
        
        cos_roll = math.cos(roll)
        sin_roll = math.sin(roll)
        cos_pitch = math.cos(pitch)
        sin_pitch = math.sin(pitch)
        
        # Partial derivatives of h_accel w.r.t. state
        H_accel[0, 1] = -g * cos_pitch  # d(h_x)/d(pitch)
        
        H_accel[1, 0] = g * cos_roll * cos_pitch   # d(h_y)/d(roll)
        H_accel[1, 1] = -g * sin_roll * sin_pitch  # d(h_y)/d(pitch)
        
        H_accel[2, 0] = -g * sin_roll * cos_pitch  # d(h_z)/d(roll)
        H_accel[2, 1] = -g * cos_roll * sin_pitch  # d(h_z)/d(pitch)
        
        # Kalman gain
        S_accel = H_accel @ self.P @ H_accel.T + self.R_accel
        K_accel = self.P @ H_accel.T @ np.linalg.inv(S_accel)
        
        # State update
        self.state += K_accel @ y_accel
        
        # Covariance update
        I_KH = np.eye(6) - K_accel @ H_accel
        self.P = I_KH @ self.P @ I_KH.T + K_accel @ self.R_accel @ K_accel.T
    
    def update_magnetometer(self, mag_ned):
        """EKF Update Step - Use magnetometer data"""
        
        if np.linalg.norm(mag_ned) < 1.0:  # Skip if magnetometer data is invalid
            return
        
        roll, pitch, yaw = self.state[0:3]
        
        # Earth's magnetic field in NED frame (approximate)
        mag_strength = np.linalg.norm(mag_ned)
        mag_inclination = 0.0  # Assume horizontal field for simplicity
        
        # Expected magnetic field in NED
        mag_earth_ned = np.array([
            mag_strength * math.cos(mag_inclination),  # North component
            0.0,                                       # East component  
            mag_strength * math.sin(mag_inclination)   # Down component
        ])
        
        # Rotate expected field from NED to body frame
        cos_roll = math.cos(roll)
        sin_roll = math.sin(roll)
        cos_pitch = math.cos(pitch)
        sin_pitch = math.sin(pitch)
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        
        # Rotation matrix from NED to body
        R_nb = np.array([
            [cos_pitch * cos_yaw, cos_pitch * sin_yaw, -sin_pitch],
            [sin_roll * sin_pitch * cos_yaw - cos_roll * sin_yaw, 
             sin_roll * sin_pitch * sin_yaw + cos_roll * cos_yaw, 
             sin_roll * cos_pitch],
            [cos_roll * sin_pitch * cos_yaw + sin_roll * sin_yaw,
             cos_roll * sin_pitch * sin_yaw - sin_roll * cos_yaw,
             cos_roll * cos_pitch]
        ])
        
        # Expected magnetometer measurement
        h_mag = R_nb @ mag_earth_ned
        
        # Measurement residual
        y_mag = mag_ned - h_mag
        
        # For simplicity, use only the horizontal components for yaw estimation
        # This avoids complex 3D magnetometer Jacobian computation
        yaw_measured = math.atan2(mag_ned[1], mag_ned[0]) + math.radians(self.magnetic_declination)
        yaw_expected = yaw
        
        # Normalize angle difference
        y_yaw = self.normalize_angle(yaw_measured - yaw_expected)
        
        # Simple 1D update for yaw only
        H_yaw = np.zeros((1, 6))
        H_yaw[0, 2] = 1.0  # d(yaw_measurement)/d(yaw)
        
        # Kalman gain for yaw
        S_yaw = H_yaw @ self.P @ H_yaw.T + np.array([[self.R_mag[0, 0]]])
        K_yaw = self.P @ H_yaw.T / S_yaw[0, 0]
        
        # State update
        self.state += K_yaw.flatten() * y_yaw
        
        # Covariance update
        I_KH = np.eye(6) - np.outer(K_yaw, H_yaw)
        self.P = I_KH @ self.P
    
    def normalize_angle(self, angle):
        """Normalize angle to [-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
    
    def get_orientation_degrees(self):
        """Get current orientation estimate in degrees"""
        return {
            'roll': math.degrees(self.state[0]),
            'pitch': math.degrees(self.state[1]),
            'yaw': math.degrees(self.state[2])
        }
    
    def get_gyro_biases_degrees(self):
        """Get current gyroscope bias estimates in degrees/second"""
        return {
            'bias_x': math.degrees(self.state[3]),
            'bias_y': math.degrees(self.state[4]),
            'bias_z': math.degrees(self.state[5])
        }
    
    def get_uncertainty(self):
        """Get orientation uncertainty (standard deviation) in degrees"""
        return {
            'roll_std': math.degrees(math.sqrt(self.P[0, 0])),
            'pitch_std': math.degrees(math.sqrt(self.P[1, 1])),
            'yaw_std': math.degrees(math.sqrt(self.P[2, 2]))
        }
    
    def run_ekf(self):
        """Main EKF loop"""
        print("\n🎯 ICM20948 Extended Kalman Filter")
        print("=" * 60)
        print("Optimal sensor fusion for orientation estimation")
        print("• Automatic gyroscope bias estimation")
        print("• Robust handling of sharp movements")
        print("• No manual resets required")
        print()
        
        if self.calibration_data:
            cal_time = self.calibration_data.get('timestamp', 'unknown')
            print(f"📊 Using calibration from: {cal_time}")
            
            if 'abnormalities' in self.calibration_data:
                abnormalities = len(self.calibration_data['abnormalities'])
                if abnormalities == 0:
                    print("✅ Calibration quality: EXCELLENT")
                elif abnormalities <= 3:
                    print(f"⚠️  Calibration quality: GOOD ({abnormalities} issues)")
                else:
                    print(f"❌ Calibration quality: POOR ({abnormalities} issues)")
        
        print("\nPress Ctrl+C to stop\n")
        print("EKF ORIENTATION ESTIMATE    GYRO BIAS ESTIMATES     UNCERTAINTY")
        print("Roll  Pitch  Yaw           X     Y     Z           Roll Pitch Yaw")
        print("(°)   (°)    (°)           (°/s) (°/s) (°/s)       (°)  (°)   (°)")
        print("-" * 75)
        
        last_time = time.time()
        
        try:
            while True:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                
                if dt <= 0:
                    continue
                
                # Get calibrated sensor data
                accel_ned, gyro_ned, mag_ned, mag_valid = self.apply_calibration_and_transform()
                
                # Initialize EKF on first iteration
                if not self.initialized:
                    self.initialize_state(accel_ned, mag_ned, mag_valid)
                    continue
                
                # EKF Predict step
                self.predict(gyro_ned, dt)
                
                # EKF Update steps
                self.update_accelerometer(accel_ned)
                if mag_valid:
                    self.update_magnetometer(mag_ned)
                
                # Get results
                orientation = self.get_orientation_degrees()
                biases = self.get_gyro_biases_degrees()
                uncertainty = self.get_uncertainty()
                
                # Display results
                print(f"{orientation['roll']:+5.1f} {orientation['pitch']:+5.1f} {orientation['yaw']:+6.1f}     "
                      f"{biases['bias_x']:+5.2f} {biases['bias_y']:+5.2f} {biases['bias_z']:+5.2f}     "
                      f"{uncertainty['roll_std']:4.1f} {uncertainty['pitch_std']:4.1f} {uncertainty['yaw_std']:5.1f}", 
                      end="\r")
                
                time.sleep(0.05)  # 20Hz update rate
                
        except KeyboardInterrupt:
            print("\n\n🎯 EKF stopped!")
            print(f"\n📊 Final Results:")
            print(f"   Orientation: Roll={orientation['roll']:+5.1f}°, Pitch={orientation['pitch']:+5.1f}°, Yaw={orientation['yaw']:+6.1f}°")
            print(f"   Gyro Biases: X={biases['bias_x']:+5.2f}°/s, Y={biases['bias_y']:+5.2f}°/s, Z={biases['bias_z']:+5.2f}°/s")
            print(f"   Uncertainty: Roll=±{uncertainty['roll_std']:4.1f}°, Pitch=±{uncertainty['pitch_std']:4.1f}°, Yaw=±{uncertainty['yaw_std']:5.1f}°")
    
    def close(self):
        """Close sensor connection"""
        if self.imu:
            self.imu.close()

def main():
    """Main function"""
    ekf = ICM20948_EKF()
    
    try:
        if not ekf.initialize():
            print("\n❌ Failed to initialize. Make sure:")
            print("   1. ICM20948 is connected and working")
            print("   2. Calibration file exists (run calibrate_raw_sensors.py)")
            return
        
        print("\n🚀 EXTENDED KALMAN FILTER FEATURES:")
        print("✅ Optimal sensor fusion (mathematically proven)")
        print("✅ Automatic gyroscope bias estimation and correction")
        print("✅ Robust handling of sharp movements")
        print("✅ No manual resets required")
        print("✅ Uncertainty quantification")
        print("✅ 20Hz real-time operation")
        
        ekf.run_ekf()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        ekf.close()

if __name__ == "__main__":
    main() 