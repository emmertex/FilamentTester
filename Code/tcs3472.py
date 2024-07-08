import machine
import time
import struct

ADDR = 0x29
LEVEL = 65535

class TCS3472:
    def __init__(self, i2c):
        self.i2c = i2c
        self.enable_sensor()
        self.led = machine.PWM(machine.Pin(8))
        self.led.freq(1000)
        self.led.duty_u16(128)

    def enable_sensor(self):
        

        # Power on and enable the sensor
        self.i2c.writeto(ADDR, b'\x80\x03')
        # Set integration time to 101 ms (0x2B)
        self.i2c.writeto(ADDR, b'\x81\x2b')
        # Set Gain
        self.i2c.writeto(ADDR, b'\x0F\x01')
        print("Sensor enabled with integration time 0x2B")

    def scaled(self):
        ## Mostly From Adafruit Library
        """Read the RGB color detected by the sensor.  Returns a 3-tuple of
        red, green, blue component values as bytes (0-255).
        """
        clear, r, g, b = self.raw()

        # Avoid divide by zero errors ... if clear = 0 return black
        if clear == 0:
            return (0, 0, 0)

        # Each color value is normalized to clear, to obtain int values between 0 and 255.
        # A gamma correction of 2.5 is applied to each value as well, first dividing by 255,
        # since gamma is applied to values between 0 and 1
        red = int(pow((int((r / clear) * 256) / 255), 2.25) * 255)
        green = int(pow((int((g / clear) * 256) / 255), 2.2) * 255)
        blue = int(pow((int((b / clear) * 256) / 255), 2.25) * 255)

        # Handle possible 8-bit overflow
        red = min(red, 255) + 3
        green = min(green, 255) - 17
        blue = min(blue, 255)
        
        ir = (red+green+blue-clear) / 2 if (red+green+blue > clear) else 0.0
        r2 = red - ir
        g2 = green - ir
        b2 = blue - ir
    
        lux = 0.136 * r2 + g2 + -.44 * b2
        
        maximum = 16000
        minimum = 3500
        minmax = maximum-minimum
        scale = (((clear - minimum) / minmax)+0.1)*16
        
        red = int(min(max((red * scale), 0), 255))
        green = int(min(max((green * scale), 0), 255))
        blue = int(min(max((blue * scale), 0), 255))
    
        return (red, green, blue, lux, clear)

    def valid(self):
        self.i2c.writeto(ADDR, b'\x93')
        return self.i2c.readfrom(ADDR, 1)[0] & 1

    def raw(self):
        self.i2c.writeto(ADDR, b'\xb4')
        data = self.i2c.readfrom(ADDR, 8)
        return struct.unpack("<HHHH", data)
