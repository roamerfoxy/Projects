"""
This module provides a class for displaying system information on an LCD screen.

It includes methods for formatting byte sizes, retrieving CPU usage,
and reading system temperature. The class is designed to work with
a Luma LCD device to render the information.

Dependencies:
- os
- time
- datetime
- luma.core
- luma.lcd
- PIL
- psutil

The main class, sysinfo_page, initializes with a device and contains
methods to gather and format system information for display.
"""

import os
import time
from datetime import datetime

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
from PIL import ImageFont
from PIL import Image

import psutil

fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)

size = 50, 50
posn = 10, 10


class SysInfoPage:
    """
    A class for displaying system information on an LCD screen.

    This class provides methods to gather and format various system information
    such as CPU usage, memory usage, disk usage, system temperature, uptime,
    and network information. It is designed to work with a Luma LCD device
    to render the information.

    Attributes:
        device: A Luma LCD device object for rendering information.

    Methods:
        bytes2human: Converts byte sizes to human-readable format.
        cpu_usage: Retrieves current CPU load.
        sys_tempc: Reads system temperature.
        sys_uptime: Calculates system uptime.
        mem_usage: Retrieves memory usage information.
        disk_usage: Retrieves disk usage information for a given path.
        network: Retrieves IP address for a given network interface.
        show: Displays the system information on the LCD screen.
    """

    def __init__(self, device):
        self.device = device

    def bytes2human(self, n):
        """
        >>> bytes2human(10000)
        '9K'
        >>> bytes2human(100001221)
        '95M'
        """
        symbols = ("K", "M", "G", "T", "P", "E", "Z", "Y")
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = int(float(n) / prefix[s])
                return f"{value}{s}"
        return f"{n}B"

    def cpu_usage(self):
        """cpu usage"""
        av1, _, _ = os.getloadavg()
        return f"Load: {av1:.1f}"

    def sys_tempc(self):
        """ ""system temperature"""
        with open(
            "/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8"
        ) as temp_file:
            temp_c = int(temp_file.read()) / 1000
        return f"TempC: {temp_c:0.1f}"

    def sys_uptime(self):
        """ ""system uptime"""
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        return f"Up-Time: {str(uptime).split('.', maxsplit=1)[0]}"

    def mem_usage(self):
        """memory usage"""
        usage = psutil.virtual_memory()
        return f"Mem: {self.bytes2human(usage.total)}  {usage.percent:.0f}%"

    def disk_usage(self, path):
        """disk usage"""
        usage = psutil.disk_usage(path)
        return f"SD: {self.bytes2human(usage.total)} {usage.percent:.0f}%"

    def network(self, iface):
        """network"""
        ip = psutil.net_if_addrs()[iface][0][1]
        return f"IP: {ip}"

    def show(self):
        """display the system information"""
        icon = Image.open("/home/pi/Projects/Images/sys_info.png")
        icon.thumbnail(size)
        background = Image.new("RGBA", self.device.size)
        background.paste(icon, posn)

        with canvas(self.device, background) as draw:

            # draw = ImageDraw.Draw(background)
            draw.text((5, 75), self.sys_uptime(), font=fnt, fill="white")
            draw.text((5, 100), self.sys_tempc(), font=fnt, fill="white")
            draw.text((5, 125), self.cpu_usage(), font=fnt, fill="white")
            draw.text((5, 150), self.mem_usage(), font=fnt, fill="white")
            draw.text((5, 175), self.disk_usage("/"), font=fnt, fill="white")
            draw.text((5, 200), self.network("wlan0"), font=fnt, fill="white")


def main():
    """main"""
    serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27)
    device = st7789(serial, rotate=1)

    page = SysInfoPage(device)

    while True:
        page.show()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
