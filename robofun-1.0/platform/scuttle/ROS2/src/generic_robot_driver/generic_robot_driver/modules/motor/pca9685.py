from .motor import Motor
import smbus2
import math
import time

class PCA9685(Motor):
    REG_MODE1 = 0x00
    REG_PRESCALE = 0xFE
    REG_LED0_ON_L = 0x06
    REG_LED0_ON_H = 0x07
    REG_LED0_OFF_L = 0x08
    REG_LED0_OFF_H = 0x09

    def __init__(self, i2c_bus_id=1, pins=[0,1], address=0x43, frequency=150):
        Motor.__init__(self, i2c_bus_id, pins, address, frequency)
        self.i2cbus = smbus2.SMBus(i2c_bus_id)
        self.pins = pins
        self.address = address
        self.register_mode = 0x00
        self.frequency = frequency
        
        self._write(self.REG_MODE1, self.register_mode)
        self._set_frequency(self.frequency)

    def _write(self, register, value):
        self.i2cbus.write_byte_data(self.address, register, value)
    
    def _read(self, register):
        return self.i2cbus.read_byte_data(self.address, register)

    def _set_frequency(self, frequency):
        prescale = 25000000.0 / 4096.0 / float(frequency) - 1.0
        prescale = math.floor(prescale + 0.5)
        old_mode = self._read(self.REG_MODE1)
        self.register_mode = (old_mode & 0x7F) | 0x10
        self._write(self.REG_MODE1, self.register_mode)
        self._write(self.REG_PRESCALE, int(math.floor(prescale)))
        self._write(self.REG_MODE1, old_mode)
        time.sleep(0.005)
        self._write(self.REG_MODE1, old_mode | 0x80)

    def set_duty(self, pin, duty):
        duty = int(duty * 4096.0 / (1.0/self.frequency * 10000000))
        self._write(self.REG_LED0_ON_L + 4 * pin, 0 & 0xFF)
        self._write(self.REG_LED0_ON_H + 4 * pin, 0 >> 8)
        self._write(self.REG_LED0_OFF_L + 4 * pin, duty & 0xFF)
        self._write(self.REG_LED0_OFF_H + 4 * pin, duty >> 8)    