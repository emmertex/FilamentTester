### Why? 
Knowing what colour, and transparency each filament is, is very difficult to do.  
Print a flat disc, and use a colourometer, then print a bunch of varying layer thicknesses and observe subjectively.

### Enter TD-1 by AJAX
So I ordered a kit, and assembled it.  Well, it had severe issues. 
A collection of Aliexpress parts wasn't the problem, the code was.  
The colour was way off.  Transmissive Distance seemed good, repeatable, but only solved half the problem.
I sent an email, I contacted them in private and public on Discord, but unfortunately AJAX had no interest in fixing the issues.  In the end I offered to help in a private message, which went ignored.
So Ignored privately sent messages, and dismissed public ones.  
![[CleanShot 2024-07-07 at 15.29.09@2x.png]]

Well, not much more I could do, than write the code from scratch.  
So this is not a fork, it is all original content, and where code is reused, all links to the github used is below. 
In fact, the entire process is below.



### Benchmark using TD-1

TD-1 Original Readings of testing filaments

| Colour  | TD  | Colour   |
| ------- | --- | -------- |
| Purple  | 4.9 | 93 C6 CB |
| Purple  | 4.8 | 94 C9 CE |
| Magenta | 3.2 | E8 7D AD |
| Magenta | 3.2 | EA 84 B3 |
| Pink    | 6.7 | FF A6 A8 |
| Pink    | 6.6 | FF A7 AB |
| Beige   | 3.5 | FF FF FF |
| Black   | 0.2 | 10 3C 1C |
| Black   | 0.1 | 11 3D 1D |

### Scan for I2C devices

```python
from machine import I2C, Pin

i2c = I2C(1, scl=Pin(27), sda=Pin(26))

# Scan for I2C devices
devices = i2c.scan()

if devices:
    print("I2C devices found:")
    for device in devices:
        print(hex(device))
else:
    print("No I2C devices found")

```

Found 3 addresses

```
0x29
0x39
0x3c
```

0x29 :  : TCS3472
0x3C : LCD : SSD1306
0x39 :  : TSL2561

### LCD Hello World

https://github.com/stlehmann/micropython-ssd1306/blob/master/ssd1306.py
```python
from machine import Pin, I2C
import ssd1306
import time

# Initialize I2C
i2c = I2C(1, scl=Pin(27), sda=Pin(26))

# Initialize the SSD1306 OLED display
# The address of the display is 0x3C
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Clear the display
oled.fill(0)

# Display "Hello World"
oled.text("Hello World", 0, 0)

# Update the display to show the text
oled.show()

```

It worked, but a bit yuck, try SH1106
https://github.com/robert-hh/SH1106/blob/master/sh1106.py
```python
from machine import Pin, I2C
import sh1106
import time

# Initialize I2C
i2c = I2C(1, scl=Pin(27), sda=Pin(26))

# Initialize the SH1106 OLED display
# The address of the display is 0x3C
oled = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3C)

# Clear the display
oled.fill(0)

# Display "Hello World"
oled.text("Hello World", 0, 0)

# Update the display to show the text
oled.show()

```

Text too small
https://github.com/peterhinch/micropython-font-to-py/tree/master/writer
```python
from machine import Pin, I2C
import sh1106
from writer import Writer
import freesans20  # Example font file
import framebuf

# Initialize I2C
i2c = I2C(1, scl=Pin(27), sda=Pin(26))

# Initialize the OLED display
oled = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3C)

# Create a Writer instance
Writer.set_textpos(oled, 0, 0)
wri = Writer(oled, freesans20, verbose=False)
wri.set_clip(False, False, False)  # Char wrap

wri.printstring("Hello World")

# Update the display to show the text
oled.show()

```

Perfect

### Read the Luminosity Sensor
https://github.com/adafruit/Adafruit_CircuitPython_TSL2561/blob/main/adafruit_tsl2561.py
Get rid of adafruit junk
```python
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
        return self.calculate_lux(broadband, infrared, ratio)

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


```

```python
from machine import Pin, I2C
import time
import tsl2561

i2c = I2C(1, scl=Pin(27), sda=Pin(26))


# Initialize the TSL2561 sensor
sensor = tsl2561.TSL2561(i2c, address=0x39)

# Configure the sensor
sensor.set_timing(integration_time=0x02, gain=0x01)  # Integration time and gain can be adjusted
sensor.power_on()
# Function to read and print light intensity
def read_tsl2561():
    lux = sensor.lux
    print("Lux: {:.2f} lux".format(lux))

# Read and print data in a loop
while True:
    read_tsl2561()
    time.sleep(1)  # Adjust the delay as needed

```

### Get colour working
TCS3474
```python
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


```

Test Code
```python
from machine import I2C, Pin
import time
import tcs3472

# Initialize I2C
i2c = I2C(1, scl=Pin(27), sda=Pin(26))

# Initialize the TCS3472 sensor
color_sensor = tcs3472.TCS3472(i2c)

# Function to read and display color data
def read_color_data():
    r, g, b, l, c = color_sensor.scaled()
    print("#{:02x}{:02x}{:02x} - {} - {}".format(int(r), int(g), int(b), l, c))

# Read and display data in a loop
while True:
    read_color_data()
    time.sleep(0.5)

```


### Get TD Working
Find the Pixels.  Not sure what they are, but start with WS281x format.
```python
import machine
import neopixel
import time

NEOPIXEL_PIN = 29 

NUM_LEDS = 2 

np = neopixel.NeoPixel(machine.Pin(NEOPIXEL_PIN), NUM_LEDS)

# Function to set the color of a single pixel
def set_pixel_color(pixel_index, color):
    np[pixel_index] = color
    np.write()

# Function to clear all pixels
def clear_pixels():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()

time.sleep(1)
set_pixel_color(1, (255, 0, 0))  # Red
time.sleep(1)
set_pixel_color(1, (0, 255, 0))  # Green
time.sleep(1)
set_pixel_color(1, (0, 0, 255))  # Blue
time.sleep(1)

clear_pixels()

time.sleep(1)
set_pixel_color(0, (255, 0, 0))  # Red
time.sleep(1)
set_pixel_color(0, (0, 255, 0))  # Green
time.sleep(1)
set_pixel_color(0, (0, 0, 255))  # Blue
time.sleep(1)

clear_pixels()


```

Now read Intensity with Beige, confirmed to be 3.5 by HueForge Creator
![[CleanShot 2024-07-07 at 15.41.11@2x.png]]

```python
import machine
import neopixel
import time
import tsl2561

NEOPIXEL_PIN = 29 

NUM_LEDS = 2

i2c = machine.I2C(1, scl=machine.Pin(27), sda=machine.Pin(26))
sensor = tsl2561.TSL2561(i2c, address=0x39)

np = neopixel.NeoPixel(machine.Pin(NEOPIXEL_PIN), NUM_LEDS, bpp=4)
sensor.power_on()

def read_tsl2561():
    lux = sensor.lux
    print("Lux: {:.2f} lux".format(lux))

def set_pixel_color(pixel_index, color):
    np[pixel_index] = color
    np.write()

# Function to clear all pixels
def clear_pixels():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0, 0)
    np.write()






# Initialize the TSL2561 sensor

# Configure the sensor
sensor.set_timing(integration_time=0x02, gain=0x01)  # Integration time and gain can be adjusted


# Read and print data in a loop
while True:
    time.sleep(1)  # Adjust the delay as needed
    read_tsl2561()
    time.sleep(1)  # Adjust the delay as needed
    set_pixel_color(1, (255, 255, 255, 255))
    time.sleep(1)  # Adjust the delay as needed
    read_tsl2561()
    clear_pixels()


```


#### Testing Filaments
| Colour | Pixel | Lux  | BB    | TD Expected |
| ------ | ----- | ---- | ----- | ----------- |
| Pink   | 64    | 1089 | 43767 | 6.6         |
| Pink   | 32    | 543  | 21816 | 6.6         |
| Purple | 64    | 638  | 24623 | 4.9         |
| Purple | 32    | 317  | 12259 | 4.9         |
|        |       |      |       |             |
So -- assume dangerously Pixel is linear for now

| Colour | Pixel | Lux  | BB    | TD Expected | ( Lux / Pixel ) / 2.578 = | ( BB / Pixel ) / 104 = |
| ------ | ----- | ---- | ----- | ----------- | ------------------------- | ---------------------- |
| Pink   | 64    | 1089 | 43767 | 6.6         | 6.6                       | 6.6                    |
| Pink   | 32    | 543  | 21816 | 6.6         | 6.6                       | 6.3                    |
| Purple | 64    | 638  | 24623 | 4.9         | 3.9                       | 3.7                    |
| Purple | 32    | 317  | 12259 | 4.9         | 3.8                       | 3.7                    |
|        |       |      |       |             |                           |                        |
So clearly -- I need to print these filaments and find the truth
#### Experiment with Purple
| Pixel Color | BB    |
| ----------- | ----- |
| Red         | 6680  |
| Green       | 4235  |
| Blue        | 12608 |
Well --- Well Well
Lets find what it's colour actually is 
Roughly D7 98 CF

Check with Color Sensor
4E 48 A3

Lets Normalise

| Colour | Subjective | BB (div 0x55) | Colour | BB (div 0x3C) |
| ------ | ---------- | ------------- | ------ | ------------- |
| Red    | D7         | 4E            | 4E     | 6F            |
| Green  | 98         | 49            | 48     | 46            |
| Blue   | CF         | 94            | A3     | D2            |
|        |            |               |        |               |
|        |            |               |        |               |

Hmm, I wonder if I can correct for this. 

| Colour | Pixel | Sub       | Reading |
| ------ | ----- | --------- | ------- |
| Red    | 48    | D7 (4300) | 4290    |
| Green  | 53    | 98 (3040) | 3010    |
| Blue   | 25    | CF (4140) | 4190    |
|        |       |           |         |
 Now we try Blue
 
|     | Colour | Pixel | Reading | Sub |
| --- | ------ | ----- | ------- | --- |
|     | Red    | 48    | 98      | 04  |
|     | Green  | 53    | 5517    | FF  |
|     | Blue   | 25    | 4246    | D4  |

This is worth integrating if it was front lighted -- let's put this on HW Revision

#### So let's tie it together
```python
import machine
import neopixel
import time
import tsl2561
import tcs3472
import sh1106

NEOPIXEL_PIN = 29 

NUM_LEDS = 2

i2c = machine.I2C(1, scl=machine.Pin(27), sda=machine.Pin(26))
sensor = tsl2561.TSL2561(i2c, address=0x39)
oled = sh1106.SH1106_I2C(128, 32, i2c, addr=0x3C)
color_sensor = tcs3472.TCS3472(i2c)
np = neopixel.NeoPixel(machine.Pin(NEOPIXEL_PIN), NUM_LEDS, bpp=4)

sensor.power_on()
sensor.set_timing(integration_time=0x02, gain=0x01)  # Integration time and gain can be adjusted


def read_tsl2561():
    lux, lum = sensor.lux
    print("Lux: {:.2f} lux ... Lum: {}".format(lux, lum))
    oled.text("TD:  {0:.1f}".format((lum / 48 ) / 104), 0,0)

def set_pixel_color(pixel_index, color):
    np[pixel_index] = color
    np.write()

def clear_pixels():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0, 0)
    np.write()

def read_color_data():
    r, g, b, l, c = color_sensor.scaled()
    print("#{:02x}{:02x}{:02x} - {} - {}".format(int(r), int(g), int(b), l, c))
    oled.text("Col: # {:02x} {:02x} {:02x}".format(int(r), int(g), int(b)), 0, 16)

while True:
    set_pixel_color(0, (0, 0, 0, 48))
    time.sleep(1)  # Adjust the delay as needed
    
    oled.fill(0)
    read_color_data()
    read_tsl2561()
    oled.show()
    clear_pixels()
    time.sleep(5)


```
