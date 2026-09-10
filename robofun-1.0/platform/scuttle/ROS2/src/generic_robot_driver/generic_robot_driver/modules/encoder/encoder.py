import smbus2
import time
from abc import abstractmethod

class Encoder:
    def __init__(self, i2c_bus_id=1, address=0x40, resolution=2**14, invert=False):
        self.i2cbus = smbus2.SMBus(i2c_bus_id)
        self.address = address
        self.invert = invert
        self.resolution = resolution
        self.position = None
        self.magnitude = None
        self.angle = None
    
    @abstractmethod
    def _read_pos(self):
        pass

    @abstractmethod
    def _read_angle(self):
        pass

    @abstractmethod
    def _read_magnitude(self):
        pass

    def read_timestamped_position(self):
        self.position = self._read_pos()
        return self.position, time.monotonic_ns()

    def read_position(self):
        self.position = self._read_pos()
        return self.position

    def read_magnitude(self):
        self._read_magnitude()
        return self.magnitude

    def read_angle(self):
        self._read_angle()
        return self.angle