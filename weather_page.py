"""
3 Day weather forecast from the BBC.
"""

import time

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
from PIL import ImageFont
from PIL import Image

import feedparser


fnt1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
fnt2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
fnt3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

fill1 = (140, 140, 140)
fill2 = (100, 100, 100)

size = 70, 70
posn = 10, 10


class WeatherPage:
    """
    Displays a 3-day weather forecast from the BBC on a display device.

    The `weather_page` class is responsible for fetching the weather data from the BBC's RSS feeds, parsing the relevant information, and rendering the forecast on the display device.

    The `show()` method is the main entry point for displaying the weather forecast. It retrieves the current temperature, location, and 3-day forecast information from the BBC's RSS feeds, and then renders the data on the display device using the Luma.LCD library.

    The method handles errors in the RSS feed responses and displays a default image if the weather data cannot be retrieved.
    """

    def __init__(self, device):
        self.device = device

    def show(self):
        """display the weather"""
        location_id = 2643743
        weather_forecast_rss_url = f"https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/{location_id}"
        weather_now_rss_url = f"https://weather-broker-cdn.api.bbci.co.uk/en/observation/rss/{location_id}"

        feed_forecast = feedparser.parse(weather_forecast_rss_url)
        feed_now = feedparser.parse(weather_now_rss_url)

        if feed_forecast.status != 200 or feed_now.status != 200:
            print(f"feed forecast status: {feed_forecast.status}")
            print(f"feed now status: {feed_now.status}")
            return

        curr_temp = feed_now["entries"][0]["title"].split(",")[1][0:4]
        loc = feed_forecast["feed"]["title"].split("for")[1].split(",")[0]

        t1_weather = feed_forecast["entries"][0]["title"].split(",")[0].split(":")[1]
        t1_low = feed_forecast["entries"][0]["title"].split(",")[1].split(":")[1][0:4]
        t1_high = (
            feed_forecast["entries"][0]["title"].split(",")[1].split(":")[2][0:4]
            if len(feed_forecast["entries"][0]["title"].split(",")[1].split(":")) == 3
            else ""
        )

        t2_weather = feed_forecast["entries"][1]["title"].split(",")[0].split(":")[1]
        t2_low = feed_forecast["entries"][1]["title"].split(",")[1].split(":")[1][0:4]
        t2_high = feed_forecast["entries"][1]["title"].split(",")[1].split(":")[2][0:4]

        t3_weather = feed_forecast["entries"][2]["title"].split(",")[0].split(":")[1]
        t3_low = feed_forecast["entries"][2]["title"].split(",")[1].split(":")[1][0:4]
        t3_high = feed_forecast["entries"][2]["title"].split(",")[1].split(":")[2][0:4]

        if "Sunny" in t1_weather:
            icon = Image.open("/home/pi/Projects/Images/sunny.png")
        elif "Cloud" in t1_weather:
            icon = Image.open("/home/pi/Projects/Images/cloudy.png")
        elif "Rain" or "Shwoers" in t1_weather:
            icon = Image.open("/home/pi/Projects/Images/rain.png")
        else:
            icon = Image.open("/home/pi/Projects/Images/sys_info.png")

        icon.thumbnail(size)
        background = Image.new("RGBA", self.device.size)
        background.paste(icon, posn)

        with canvas(self.device, background) as draw:

            # draw = ImageDraw.Draw(background)
            draw.text((80, 30), curr_temp, font=fnt3, fill="white")
            draw.text((150, 45), loc, font=fnt1, fill="white")
            draw.text((10, 80), t1_weather, font=fnt2, fill="white")
            draw.text((10, 110), f"{t1_low} - {t1_high}", font=fnt2, fill="white")
            draw.text((10, 150), t2_weather, font=fnt1, fill="white")
            draw.text((10, 170), f"{t2_low} - {t2_high}", font=fnt1, fill="white")
            draw.text((10, 190), t3_weather, font=fnt1, fill="white")
            draw.text((10, 210), f"{t3_low} - {t3_high}", font=fnt1, fill="white")


def main():
    """main"""
    serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27)
    device = st7789(serial, rotate=1)

    page = WeatherPage(device)

    while True:
        page.show()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
