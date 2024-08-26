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


from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from RPi import GPIO

import sysinfo_page
import datetime_page
import weather_page
import deskinfo_page
import desk


class PiController:
    """
    Main controller class for the LCD display system.

    This class initializes the LCD display, sets up different pages for display,
    and handles joystick and button inputs for navigation and control. It also
    initializes the desk control system.

    Attributes:
        serial (spi): SPI interface for the display.
        display_device (st7789): LCD display device.
        page0 (SysInfoPage): Page for system information.
        page1 (DatetimePage): Page for date and time display.
        page2 (WeatherPage): Page for weather information.
        page3 (DeskInfoPage): Page for desk information.
        ikea_desk (Desk): Desk control object.
        pages (list): List of all page objects.
        current_page (int): Index of the currently displayed page.
        loop (asyncio.AbstractEventLoop): The asyncio event loop.

    Methods:
        js_left_callback: Handles left joystick movement.
        js_right_callback: Handles right joystick movement.
        js_down_callback: Handles downward joystick movement.
        button_one_callback: Handles button one press.
        button_two_callback: Handles button two press.
        button_three_callback: Handles button three press.
    """

    def __init__(self):
        self.serial = spi(
            port=0, device=0, gpio_DC=25, gpio_RST=27, bus_speed_hz=52000000
        )

        self.display_device = st7789(self.serial, rotate=1)

        self.page0 = sysinfo_page.SysInfoPage(self.display_device)
        self.page1 = datetime_page.DatetimePage(self.display_device)
        self.page2 = weather_page.WeatherPage(self.display_device)
        self.page3 = deskinfo_page.DeskInfoPage(self.display_device)
        self.ikea_desk = desk.Desk()
        self.pages = [self.page0, self.page1, self.page2, self.page3]

        self.current_page = 1
        self.loop = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # joystick left
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # joystick right
        GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # joystick down

        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(5, GPIO.RISING, callback=self.js_left_callback)
        GPIO.add_event_detect(26, GPIO.RISING, callback=self.js_right_callback)
        GPIO.add_event_detect(13, GPIO.RISING, callback=self.js_down_callback)
        GPIO.add_event_detect(21, GPIO.RISING, callback=self.button_one_callback)
        GPIO.add_event_detect(20, GPIO.RISING, callback=self.button_two_callback)
        GPIO.add_event_detect(16, GPIO.RISING, callback=self.button_three_callback)

    def js_left_callback(self, channel):
        """
        Callback function for left joystick movement.

        This function decrements the current page index, wrapping around to the last page
        if the current page is the first one. It then prints the channel and current page.

        Args:
            channel (int): The GPIO channel that triggered the callback.

        Returns:
            None
        """

        self.current_page -= 1
        if self.current_page < 0:
            self.current_page = 2
        print(f"channel: {channel}, current page: {self.current_page}")

    def js_right_callback(self, channel):
        """
        Callback function for right joystick movement.

        This function increments the current page index, wrapping around to the first page
        if the current page is the last one. It then prints the channel and current page.

        Args:
            channel (int): The GPIO channel that triggered the callback.

        Returns:
            None
        """

        self.current_page += 1
        if self.current_page > 2:
            self.current_page = 0
        print(f"channel: {channel}, current page: {self.current_page}")

    def js_down_callback(self, channel):
        """
        Callback function for down joystick movement.

        This function sets the current page to 1 and prints the channel and current page.

        Args:
            channel (int): The GPIO channel that triggered the callback.

        Returns:
            None
        """

        self.current_page = 1
        print(f"channel: {channel}, current page: {self.current_page}")

    def button_one_callback(self, channel):
        """
        Callback function for button one press.

        This function sets the current page to 3, waits for 1 second, and then
        moves the IKEA desk to position 3 if an event loop is available.
        It updates the desk height on page 3 and prints the channel and current page.

        Args:
            channel (int): The GPIO channel that triggered the callback.

        Returns:
            None
        """

        self.current_page = 3
        time.sleep(1)

        if self.loop is not None:
            asyncio.run_coroutine_threadsafe(
                self.ikea_desk.move_desk_to_position(
                    "position_3", self.page3.update_desk_height
                ),
                self.loop,
            )
        print(f"channel: {channel}, current page: {self.current_page}")

    def button_two_callback(self, channel):
        """
        Callback function for button two press.

        This function sets the current page to 3, waits for 1 second, and then
        moves the IKEA desk to position 2 if an event loop is available.
        It updates the desk height on page 3 and prints the channel and current page.

        Args:
            channel (int): The GPIO channel that triggered the callback.

        Returns:
            None
        """

        self.current_page = 3
        time.sleep(1)

        if self.loop is not None:
            asyncio.run_coroutine_threadsafe(
                self.ikea_desk.move_desk_to_position(
                    "position_2", self.page3.update_desk_height
                ),
                self.loop,
            )
        print(f"channel: {channel}, current page: {self.current_page}")

    def button_three_callback(self, channel):
        """
        Callback function for button three press.

        This function sets the current page to 3, waits for 1 second, and then
        moves the IKEA desk to position 1 if an event loop is available.
        It updates the desk height on page 3 and prints the channel and current page.

        Args:
            channel (int): The GPIO channel that triggered the callback.

        Returns:
            None
        """
        self.current_page = 3
        time.sleep(1)

        if self.loop is not None:
            asyncio.run_coroutine_threadsafe(
                self.ikea_desk.move_desk_to_position(
                    "position_1", self.page3.update_desk_height
                ),
                self.loop,
            )
        print(f"channel: {channel}, current page: {self.current_page}")

    def display_page(self):
        """
        Continuously displays the current page.

        This function runs in a loop, checking the current page and displaying it.
        If the current page is 3 and the desk height is "Done", it switches to page 1
        and resets the desk height to "Initializing".

        Returns:
            None
        """
        while True:
            if self.current_page in [0, 1, 2, 3]:
                # print(f'display_page: {threading.current_thread()}')
                if self.current_page == 3 and self.pages[3].desk_height == "Done":
                    self.current_page = 1
                    self.pages[3].desk_height = "Initializing"
                self.pages[self.current_page].show()
            time.sleep(0.5)

    async def async_display_page(self):
        """
        Asynchronously runs the display_page function.

        This function sets up the event loop and runs the display_page function
        in a separate executor.

        Returns:
            None
        """
        self.loop = asyncio.get_running_loop()
        await self.loop.run_in_executor(None, self.display_page)


async def main(ctrl):
    """
    Main asynchronous function to initialize and run the controller.

    This function scans for the IKEA desk, connects to it, and starts
    the asynchronous display page function.

    Args:
        ctrl: The controller object.

    Returns:
        None
    """
    await ctrl.ikea_desk.scan(ctrl.ikea_desk.config["mac_address"])
    await ctrl.ikea_desk.connect()

    await asyncio.gather(ctrl.async_display_page())


def exit_gracefully(signum, frame):
    """
    Signal handler for graceful exit.

    This function raises a KeyboardInterrupt when called, allowing for
    graceful termination of the program.

    Args:
        signum: The signal number.
        frame: The current stack frame.

    Raises:
        KeyboardInterrupt
    """
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    try:
        controller = PiController()
        asyncio.run(main(controller))
    except KeyboardInterrupt as err:
        controller.display_device.cleanup()
        GPIO.cleanup()
