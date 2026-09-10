import numpy as np
import smbus2 
from .encoder import Encoder

class AMS(Encoder):
    def __init__(self, i2c_bus_id=1, address=0x40, resolution=2**14, invert=False):
        Encoder.__init__(self, i2c_bus_id, address, resolution, invert)
        self.i2cbus = smbus2.SMBus(i2c_bus_id)
        self.address = address
        self.invert = invert
        self.resolution = resolution
        self.position = self._read_pos()
        self.angle = self._read_angle()
        self.magnitude = self._read_magnitude()

    def _read_pos(self):
        pos = self.i2cbus.read_i2c_block_data(self.address, 0xFE, 2)  
        self.position = (pos[0] << 6) | pos[1]                        
        return (self.resolution - self.position) if self.invert else self.position

    def _read_magnitude(self):
        mag = self.i2cbus.read_i2c_block_data(self.address, 0xFC, 2)
        return (mag[0] << 6) | mag[1]

    def _read_angle(self):
        self._read_pos()
        return self.position * ((2*np.pi)/self.resolution)

    