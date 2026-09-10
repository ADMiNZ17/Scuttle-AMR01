#!/usr/bin/env python3
import time
import math
import smbus2

# --- CONFIGURATION (From your ROS2 Modules) ---
I2C_BUS_ID = 13        # Adjust based on robot_driver.yaml or i2cdetect -l
PCA9685_ADDR = 0x43   # From your PCA9685 implementation
FREQUENCY = 150       # 150 Hz

# Pin configurations from your RobotDriver
LEFT_PINS = [0, 1]
RIGHT_PINS = [2, 3]

# Kinematics constraints (using realistic defaults since constants.py wasn't fully shown)
ROBOT_BASE = 0.2         # Distance between wheels in meters
ROBOT_WHEEL_RADIUS = 0.03 # Wheel radius in meters

class MockPCA9685:
    """Standalone driver using your exact math formulation to print and send I2C packets."""
    REG_MODE1 = 0x00
    REG_PRESCALE = 0xFE
    REG_LED0_ON_L = 0x06
    
    def __init__(self, bus_id, address, freq):
        self.address = address
        self.freq = freq
        print(f"[INIT] Opening I2C Bus {bus_id} at Address 0x{address:02X}...")
        try:
            self.bus = smbus2.SMBus(bus_id)
            # Initialize PCA9685
            self._write(self.REG_MODE1, 0x00)
            prescale = math.floor(25000000.0 / 4096.0 / float(freq) - 1.0 + 0.5)
            self._write(self.REG_PRESCALE, int(prescale))
            print("[INIT] I2C Device successfully initialized.")
        except Exception as e:
            print(f"[WARN] Physical I2C Bus unavailable ({e}). Running in SIMULATION mode.")
            self.bus = None

    def _write(self, reg, val):
        if self.bus:
            self.bus.write_byte_data(self.address, reg, val)

    def set_pwm_duty(self, pin, raw_speed):
        # Your exact formula: maps 0-65535 target speed into 12-bit PCA9685 steps
        duty_step = int(raw_speed * 4096.0 / (1.0 / self.freq * 10000000))
        
        on_l = 0 & 0xFF
        on_h = 0 >> 8
        off_l = duty_step & 0xFF
        off_h = duty_step >> 8
        
        # Physical writes
        self._write(self.REG_LED0_ON_L + 4 * pin, on_l)
        self._write(self.REG_LED0_ON_L + 4 * pin + 1, on_h)
        self._write(self.REG_LED0_ON_L + 4 * pin + 2, off_l)
        self._write(self.REG_LED0_ON_L + 4 * pin + 3, off_h)
        
        # Return formatted hex packet visualization for log tracking
        return f"Pin {pin} -> Regs[0x{self.REG_LED0_ON_L + 4 * pin:02X}-0x{self.REG_LED0_ON_L + 4 * pin + 3:02X}] | Payload Hex: [{on_l:02X} {on_h:02X} {off_l:02X} {off_h:02X}] (Step Value: {duty_step})"

    def calculate_motor_hw231(self, pins, angular_velocity):
        """Calculates and drives using the hw231 motor logic rules."""
        duty = round(sorted((-1, float(0.1 * angular_velocity), 1))[1], 2)
        current_duty = duty * 100
        current_speed = abs(int(duty * 0xFFFF))
        
        packets = []
        if current_duty == 0:
            packets.append(self.set_pwm_duty(pins[0], 0))
            packets.append(self.set_pwm_duty(pins[1], 0))
        else:
            if current_duty > 0:
                packets.append(self.set_pwm_duty(pins[0], current_speed))
                packets.append(self.set_pwm_duty(pins[1], 0))
            else:
                packets.append(self.set_pwm_duty(pins[0], current_speed))
                packets.append(self.set_pwm_duty(pins[1], 65535))
        return duty, packets

# --- INVERSE KINEMATICS ---
def cmd_vel_to_wheel_speeds(linear_x, angular_z):
    base_len = ROBOT_BASE / 2
    # Base configuration mapping matrix
    left_target = (linear_x - base_len * angular_z) / ROBOT_WHEEL_RADIUS
    right_target = (linear_x + base_len * angular_z) / ROBOT_WHEEL_RADIUS
    return left_target, right_target

# --- TEST RUNNER ---
def run_diagnostic():
    driver = MockPCA9685(I2C_BUS_ID, PCA9685_ADDR, FREQUENCY)
    
    # Test cases representing common cmd_vel inputs
    test_vectors = [
        ("FORWARD",          0.2,  0.0),
        ("REVERSE",         -0.2,  0.0),
        ("SHARP LEFT TURN",  0.0,  1.5),
        ("SHARP RIGHT TURN", 0.0, -1.5),
        ("STOP/BRAKE",       0.0,  0.0)
    ]
    
    print("\n" + "="*80)
    print("                      I2C DRIVER & KINEMATICS LOG REPORT               ")
    print("="*80)
    
    for name, x, z in test_vectors:
        print(f"\n[COMMAND] Input cmd_vel -> Linear X: {x} m/s | Angular Z: {z} rad/s ({name})")
        
        # 1. Compute kinematics
        left_vel, right_vel = cmd_vel_to_wheel_speeds(x, z)
        print(f"  -> Calculated Target Wheel Rad/s: Left={left_vel:.2f}, Right={right_vel:.2f}")
        
        # 2. Run through hw231 layout calculations
        left_duty, left_packets = driver.calculate_motor_hw231(LEFT_PINS, left_vel)
        right_duty, right_packets = driver.calculate_motor_hw231(RIGHT_PINS, right_vel)
        
        print(f"  -> Calculated Motor Duties:      Left={left_duty:+.2f}, Right={right_duty:+.2f}")
        print("  -> Outgoing Linux I2C Packets:")
        for pkt in left_packets:
            print(f"     [Left Wheel]  {pkt}")
        for pkt in right_packets:
            print(f"     [Right Wheel] {pkt}")
            
        time.sleep(1.0)
    print("\n" + "="*80)

if __name__ == "__main__":
    run_diagnostic()
