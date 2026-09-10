import time
import threading
import numpy as np
import subprocess
import os
from .constants import ROBOT_BASE, ROBOT_WHEEL_RADIUS, MOTOR_WHEEL_RATIO, ENCODER_RESOLUTION
from .motor import Motor
from .encoder import Encoder

class MotorEncoder:
    def __init__(self, i2c_bus_id, motor_addr, motor_pins, encoder_addr, encoder_invert=False, motor_type="hw231"):
        self.motor = Motor(i2c_bus_id, pins=motor_pins, address=motor_addr)
        self.encoder = Encoder(i2c_bus_id, address=encoder_addr, resolution=ENCODER_RESOLUTION, invert=encoder_invert)
        self.position_prev, self.timestamp_prev = self.encoder.read_timestamped_position()
        self.position, self.timestamp = self.encoder.read_timestamped_position()
        self.angular_velocity = 0
        self.linear_velocity = 0
        self.target_linear_velocity = 0
        self.target_angular_velocity = 0
        self.duty = 0
        self.radius = ROBOT_WHEEL_RADIUS
        self.mToWGear_ratio = MOTOR_WHEEL_RATIO
        self.mToWGear_rollover = self.mToWGear_ratio * ENCODER_RESOLUTION
        self.motor_type = motor_type

        self.get_latest_position()

    def set_angular_velocity(self, angular_velocity):
        self.target_angular_velocity = angular_velocity
        self.duty = 0.1 * self.target_angular_velocity

        if self.motor_type == "hw231":
            self.motor.move_hw231(self.duty)
        elif self.motor_type == "md10cr3":
            self.motor.move_md10cr3(self.duty)

    def get_angular_velocity(self):
        try:
            time_diff = self.timestamp - self.timestamp_prev
            return ((self.get_rotation() * (np.pi/(self.encoder.resolution/2))) / (time_diff/ 1e9)) 
        except ZeroDivisionError:
            return 0
            
    def get_latest_position(self):
        self.position_prev = self.position
        self.timestamp_prev = self.timestamp
        self.position, self.timestamp = self.encoder.read_timestamped_position()

    def get_rotation(self):
        rotation = self.position - self.position_prev
        if(self.mToWGear_rollover <= -rotation):
            return (rotation + self.encoder.resolution) * self.mToWGear_ratio
        if(self.mToWGear_rollover <= rotation):
            return (rotation - self.encoder.resolution) * self.mToWGear_ratio
        return rotation * self.mToWGear_ratio

    def get_distance(self):
        return (2 * np.pi * self.radius) * (self.get_rotation() / self.encoder.resolution)

    def stop(self):
        self.motor.stop()

class RobotDriver:
    def __init__(self, motor_addrs=[0x43, [0, 1], [2, 3]], encoder_addrs=[0x40, 0x41], hz=10, motor_type="hw231"):
        self.heading = 0
        self.heading_offset = 0
        self.velocity = 0
        self.angular_velocity = 0
        self.global_position = [ 0.0 , 0.0 ]
        self.i2c_bus_id = self.retrieve_i2c_id()

        self.robot_base = ROBOT_BASE
        self.robot_wheel_radius = ROBOT_WHEEL_RADIUS

        self.left_motor = MotorEncoder(self.i2c_bus_id, motor_addr=motor_addrs[0], motor_pins=motor_addrs[1], encoder_addr=encoder_addrs[0], encoder_invert=True, motor_type=motor_type)
        self.right_motor = MotorEncoder(self.i2c_bus_id, motor_addr=motor_addrs[0], motor_pins=motor_addrs[2], encoder_addr=encoder_addrs[1], encoder_invert=False, motor_type=motor_type)
        
        self.stop_move = False
        self.rate = hz
        self.wait_time = 1 / self.rate

        self.robotMoveThread = threading.Thread(target=self._move_thread)  
        self.robotMoveThread.start()                                      

    def _move_thread(self):
        while not self.stop_move:
            start_time = time.monotonic_ns()
            self._calculate_robot_position()
            time.sleep(sorted([self.wait_time-((time.monotonic_ns()-start_time)/1e9), 0])[1])

        self.left_motor.stop()
        self.right_motor.stop()

    def _set_kinematic_move_calculation(self, movement):
        base_length = self.robot_base / 2        
        base_to_wheel = np.array([[ 1 / self.robot_wheel_radius, -base_length / self.robot_wheel_radius ],
                      [ 1 / self.robot_wheel_radius, base_length / self.robot_wheel_radius]])
        base_speed = np.array([movement[0], movement[1]])
        return np.matmul(base_to_wheel, base_speed)
    
    def _get_kinematic_move_calculation(self):
        A = self.robot_wheel_radius / 2
        B = self.robot_wheel_radius / self.robot_base
        mAB = np.array([[ A, A ], [ -B, B ]])
        mC = np.array([self.left_motor.get_angular_velocity(), self.right_motor.get_angular_velocity()])
        mABC = np.matmul(mAB, mC)
        self.velocity = mABC[0]
        self.angular_velocity = mABC[1]
        return [self.velocity, self.angular_velocity]

    def _calculate_robot_position(self):
        self.left_motor.get_latest_position()
        self.right_motor.get_latest_position()
        self.velocity, self.angular_velocity = self._get_kinematic_move_calculation()
        left_wheel_distance = self.left_motor.get_distance()
        right_wheel_distance = self.right_motor.get_distance()
        base_travel_distance = (left_wheel_distance + right_wheel_distance) / 2
        self.global_position[0] = self.global_position[0] + (base_travel_distance * np.cos(self.heading)) # X
        self.global_position[1] = self.global_position[1] + (base_travel_distance * np.sin(self.heading)) # Y
        self.heading = self.heading + ((right_wheel_distance - left_wheel_distance) / self.robot_base)

    def get_left_motor_encoder_position(self):
        return self.left_motor.encoder.position * ((2 * np.pi) / ENCODER_RESOLUTION)

    def get_right_motor_encoder_position(self):
        return self.right_motor.encoder.position * ((2 * np.pi) / ENCODER_RESOLUTION)

    def get_encoder_resolution(self):
        return ENCODER_RESOLUTION

    def move(self, movement):
        target_speed = self._set_kinematic_move_calculation(movement)
        self.left_motor.set_angular_velocity(target_speed[1])
        self.right_motor.set_angular_velocity(target_speed[0])

    def get_robot_metadata(self):
        movement = self._get_kinematic_move_calculation()
        heading = self.heading
        return (self.global_position[0], self.global_position[1]), (movement[0], movement[1]), heading

    def stop(self):
        self.stop_move = True

    def retrieve_i2c_id(self):
        detect_result = subprocess.run(['i2cdetect', '-l'], stdout=subprocess.PIPE)
        if 'i2c-tiny-usb' in detect_result.stdout.decode():
            i2c_device = subprocess.run(['grep', 'i2c-tiny-usb'], input=detect_result.stdout, stdout=subprocess.PIPE)
            i2c_bus = subprocess.run(['awk', '{print $1}'], input=i2c_device.stdout, stdout=subprocess.PIPE).stdout.decode()
            return int(i2c_bus.split('-')[1].strip())
        else:
            return 1
