from modules.robot_base import RobotDriver, MotorEncoder
import time

I2C_BUS_ID = 2

def main():
    lwh = MotorEncoder(I2C_BUS_ID, 0x43, [1,0], 0x40)
    rwh = MotorEncoder(I2C_BUS_ID, 0x43, [3,2], 0x41)

    lwh.set_angular_velocity(15)
    rwh.set_angular_velocity(-15)
    time.sleep(5)
    lwh.set_angular_velocity(0)
    rwh.set_angular_velocity(0)

if __name__ == '__main__':
    main()
    