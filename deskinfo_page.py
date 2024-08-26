"""
This module implements a desk information page for a display device.

It uses the luma.lcd library to render information about desk height
on an ST7789 LCD display. The main components are:

- deskinfo_page: A class that manages the display of desk height information.
- main: A function that initializes the display and runs the main loop.

The module can be run as a standalone script to continuously display
the desk height information.
"""

import time

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
from PIL import ImageFont

fnt1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
fnt2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
fill1 = (140, 140, 140)


class DeskInfoPage:
    """
    A class that manages the display of desk height information on an LCD screen.

    This class is responsible for initializing the display device, updating
    the desk height, and rendering the information on the screen.

    Attributes:
        device: The LCD display device.
        desk_height (str): The current height of the desk.

    Methods:
        update_desk_height(desk_height): Updates the current desk height.
        show(): Renders the desk height information on the LCD screen.
    """

    def __init__(self, device):
        self.device = device
        self.desk_height = "initializing"

    def update_desk_height(self, desk_height):
        """update desk height"""
        self.desk_height = desk_height

    def show(self):
        """display the desk height"""
        with canvas(self.device) as draw:
            draw.rectangle(((0, 50), (150, 75)), fill1)
            draw.text((0, 50), "Desk Height:", font=fnt1, fill="black")
            draw.text((0, 80), self.desk_height, font=fnt2)


def main():
    """main"""
    serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27)
    device = st7789(serial, rotate=1)

    page = DeskInfoPage(device)

    while True:
        page.show()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
