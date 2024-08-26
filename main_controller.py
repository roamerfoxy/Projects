"""
Main controller module for the LCD display system.

This module initializes the LCD display, sets up different pages for display,
and handles joystick input for page navigation. It also initializes the desk
control system.

The module uses asyncio for asynchronous operation and includes the following
main components:
- LCD display initialization using SPI
- Page objects for different display content (system info, date/time, weather, desk info)
- Joystick input handling for page navigation
- Desk control initialization

Global variables:
- current_page: Tracks the currently displayed page
- loop: The asyncio event loop

Functions:
- js_left_callback: Handles left joystick movement
- js_right_callback: Handles right joystick movement

Dependencies:
- luma.core and luma.lcd for display control
- RPi.GPIO for GPIO control
- Custom modules for different pages and desk control
"""

import asyncio
import time
import signal

# import threading

from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from RPi import GPIO

import sysinfo_page
import datetime_page
import weather_page
import deskinfo_page
import desk


serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27, bus_speed_hz=52000000)
display_device = st7789(serial, rotate=1)

page0 = sysinfo_page.SysInfoPage(display_device)
page1 = datetime_page.DatetimePage(display_device)
page2 = weather_page.WeatherPage(display_device)
page3 = deskinfo_page.DeskInfoPage(display_device)
ikea_desk = desk.Desk()

pages = [page0, page1, page2, page3]
current_page = 1
loop = None


def js_left_callback(channel):
    global current_page
    current_page -= 1
    if current_page < 0:
        current_page = 2
    print(f"channel: {channel}, current page: {current_page}")


def js_right_callback(channel):
    global current_page
    current_page += 1
    if current_page > 2:
        current_page = 0
    print(f"channel: {channel}, current page: {current_page}")


def js_down_callback(channel):
    global current_page
    current_page = 1
    print(f"channel: {channel}, current page: {current_page}")


def button_one_callback(channel):
    global current_page
    global loop
    current_page = 3
    time.sleep(1)
    # asyncio.run(desk.pos_3(page3.update_desk_height))
    # print(f'button_one_callback: {threading.current_thread()}')
    if loop is not None:
        asyncio.run_coroutine_threadsafe(
            ikea_desk.move_desk_to_position("position_3", page3.update_desk_height),
            loop,
        )
    print(f"channel: {channel}, current page: {current_page}")


def button_two_callback(channel):
    global current_page
    global loop
    current_page = 3
    time.sleep(1)
    # asyncio.run(desk.pos_2(page3.update_desk_height))
    # print(f'button_two_callback: {threading.current_thread()}')
    if loop is not None:
        asyncio.run_coroutine_threadsafe(
            ikea_desk.move_desk_to_position("position_2", page3.update_desk_height),
            loop,
        )
    print(f"channel: {channel}, current page: {current_page}")


def button_three_callback(channel):
    global current_page
    global loop
    current_page = 3
    time.sleep(1)
    # asyncio.run(desk.pos_1(page3.update_desk_height))
    # print(f'button_three_callback: {threading.current_thread()}')
    if loop is not None:
        asyncio.run_coroutine_threadsafe(
            ikea_desk.move_desk_to_position("position_1", page3.update_desk_height),
            loop,
        )
    print(f"channel: {channel}, current page: {current_page}")


GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # joystick left
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # joystick right
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # joystick down

GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(5, GPIO.RISING, callback=js_left_callback)
GPIO.add_event_detect(26, GPIO.RISING, callback=js_right_callback)
GPIO.add_event_detect(13, GPIO.RISING, callback=js_down_callback)

GPIO.add_event_detect(21, GPIO.RISING, callback=button_one_callback)
GPIO.add_event_detect(20, GPIO.RISING, callback=button_two_callback)
GPIO.add_event_detect(16, GPIO.RISING, callback=button_three_callback)


def display_page():
    global current_page
    global pages
    # global loop

    while True:
        if current_page in [0, 1, 2, 3]:
            # print(f'display_page: {threading.current_thread()}')
            if current_page == 3 and pages[3].desk_height == "Done":
                current_page = 1
                pages[3].desk_height = "Initializing"
            pages[current_page].show()
        time.sleep(0.5)


async def async_display_page():
    global loop
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, display_page)


async def main():
    await ikea_desk.scan(ikea_desk.config["mac_address"])
    await ikea_desk.connect()

    await asyncio.gather(async_display_page())


def exit_gracefully(signum, frame):
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    try:
        # print(f'main: {threading.current_thread()}')
        asyncio.run(main())
    except KeyboardInterrupt as err:
        display_device.cleanup()
        GPIO.cleanup()
