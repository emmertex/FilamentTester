from machine import I2C
from micropython import const
import time

# TSL2561 default address
TSL2561_I2C_ADDR = const(0x29)

# TSL2561 Command Bits
_COMMAND_BIT = const(0x80)
_WORD_BIT = const(0x20)

# Control register values
_CONTROL_POWERON = const(0x03)
_CONTROL_POWEROFF = const(0x00)

# TSL2561 Registers
_REGISTER_CONTROL = const(0x00)
_REGISTER_TIMING = const(0x01)
_REGISTER_CHAN0_LOW = const(0x0C)
_REGISTER_CHAN1_LOW = const(0x0E)

# Gain and Timing
_GAIN_SCALE = (16, 1)
_TIME_SCALE = (1 / 0.034, 1 / 0.252, 1)
_CLIP_THRESHOLD = (4900, 37000, 65000)

class TSL2561:
    def __init__(self, i2c, address=TSL2561_I2C_ADDR):
        self.i2c = i2c
        self.address = address
        self.power_on()

    def power_on(self):
        self.i2c.writeto_mem(self.address, _COMMAND_BIT | _REGISTER_CONTROL, bytearray([_CONTROL_POWERON]))

    def power_off(self):
        self.i2c.writeto_mem(self.address, _COMMAND_BIT | _REGISTER_CONTROL, bytearray([_CONTROL_POWEROFF]))

    def set_timing(self, integration_time, gain):
        self.i2c.writeto_mem(self.address, _COMMAND_BIT | _REGISTER_TIMING, bytearray([integration_time | (gain << 4)]))

    def read_luminosity(self):
        ch0 = self.i2c.readfrom_mem(self.address, _COMMAND_BIT | _WORD_BIT | _REGISTER_CHAN0_LOW, 2)
        ch1 = self.i2c.readfrom_mem(self.address, _COMMAND_BIT | _WORD_BIT | _REGISTER_CHAN1_LOW, 2)
        return (ch0[1] << 8 | ch0[0]), (ch1[1] << 8 | ch1[0])

    @property
    def lux(self):
        broadband, infrared = self.read_luminosity()
        ratio = infrared / broadband if broadband else 0
        return self.calculate_lux(broadband, infrared, ratio), broadband

    def calculate_lux(self, broadband, infrared, ratio):
        if ratio <= 0.5:
            return 0.0304 * broadband - 0.062 * broadband * (ratio ** 1.4)
        elif ratio <= 0.61:
            return 0.0224 * broadband - 0.031 * infrared
        elif ratio <= 0.8:
            return 0.0128 * broadband - 0.0153 * infrared
        elif ratio <= 1.3:
            return 0.00146 * broadband - 0.00112 * infrared
        else:
            return 0
