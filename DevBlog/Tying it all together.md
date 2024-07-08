
Now read Intensity with Beige, confirmed to be 3.5 by HueForge Creator
![](Images/CleanShot%202024-07-08%20at%2009.51.08.png)

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
sensor.set_timing(integration_time=0x02, gain=0x01) 


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
    time.sleep(1)  
    
    oled.fill(0)
    read_color_data()
    read_tsl2561()
    oled.show()
    clear_pixels()
    time.sleep(5)



```