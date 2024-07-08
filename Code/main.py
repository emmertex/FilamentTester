import machine
import neopixel
import time
import tsl2561
import tcs3472
import sh1106
import ssd1306

NEOPIXEL_PIN = 29 

NUM_LEDS = 2

i2c = machine.I2C(1, scl=machine.Pin(27), sda=machine.Pin(26))
sensor = tsl2561.TSL2561(i2c, address=0x39)
oled = ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3C)
color_sensor = tcs3472.TCS3472(i2c)
np = neopixel.NeoPixel(machine.Pin(NEOPIXEL_PIN), NUM_LEDS, bpp=4)

sensor.power_on()
sensor.set_timing(integration_time=0x02, gain=0x01)  # Integration time and gain does not seem to work


def read_tsl2561():
    lux, lum = sensor.lux
    print("Lux: {:.2f} lux ... Lum: {}".format(lux, lum))
    oled.text("TD:  {0:.1f}".format((lum / 48 ) / 90), 0,0)

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
    oled.text("Col: # {:02x}{:02x}{:02x}".format(int(r), int(g), int(b)), 0, 16)

while True:
    set_pixel_color(0, (0, 0, 0, 48))
    time.sleep(1)
    oled.fill(0)
    read_tsl2561()
    clear_pixels()
    time.sleep(0.1)
    time.sleep(1) 
    read_color_data()
    
    oled.show()
    
    time.sleep(5)

