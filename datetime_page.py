"""
This module defines the datetime_page class for displaying date and time information on an LCD screen.

The datetime_page class uses the luma.lcd library to render date and time information
on an ST7789 LCD device. It displays the current date, weekday, and time in a
formatted layout with custom fonts and colors.

Classes:
    datetime_page: Handles the rendering of date and time information on the LCD.

Dependencies:
    - time
    - datetime
    - luma.core.interface.serial
    - luma.core.render
    - luma.lcd.device
    - PIL
"""

import time
import datetime

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
from PIL import ImageFont


fnt1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
fnt2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

fill1 = (140, 140, 140)
fill2 = (100, 100, 100)


class DatetimePage:
    """
    A class for displaying date and time information on an LCD screen.

    This class uses the luma.lcd library to render date and time information
    on an ST7789 LCD device. It displays the current date, weekday, and time
    in a formatted layout with custom fonts and colors.

    Attributes:
        device (luma.lcd.device.st7789): The LCD device to render on.
        sec_flag (int): A flag to alternate the display of seconds indicator.

    Methods:
        __init__(device): Initializes the datetime_page with the given device.
        show(): Renders the current date and time information on the LCD screen.
    """

    def __init__(self, device):
        self.device = device
        self.sec_flag = 0

    def show(self):
        """display the date and time"""
        now = datetime.datetime.now()
        today_date = now.strftime("%d %b")
        today_weekday = now.strftime("%a")
        today_time = now.strftime("%H:%M:%S")
        t1 = today_time.split(":")[0][0]
        t2 = today_time.split(":")[0][1]
        t3 = today_time.split(":")[1][0]
        t4 = today_time.split(":")[1][1]

        sec = today_time.split(":")[2][1]
        self.sec_flag = int(sec) % 2

        with canvas(self.device) as draw:

            draw.rectangle(((0, 80), (50, 130)), fill1)
            draw.rectangle(((60, 80), (110, 130)), fill1)
            draw.rectangle(((130, 80), (180, 130)), fill1)
            draw.rectangle(((190, 80), (240, 130)), fill1)

            draw.text((10, 85), t1, font=fnt1, fill="black")
            draw.text((70, 85), t2, font=fnt1, fill="black")
            draw.text((140, 85), t3, font=fnt1, fill="black")
            draw.text((200, 85), t4, font=fnt1, fill="black")

            if self.sec_flag:
                draw.ellipse((115, 90, 123, 98), fill="orange")
                draw.ellipse((115, 110, 123, 118), fill="orange")

            draw.rectangle(((130, 150), (210, 185)), fill=fill2)
            draw.text((0, 150), today_date, font=fnt2, fill=fill2)
            draw.text((135, 150), today_weekday, font=fnt2, fill="black")


def main():
    """main"""
    serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27)
    device = st7789(serial, rotate=1)

    page = DatetimePage(device)

    while True:
        page.show()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
