"""desk model"""

import functools
import asyncio
import os
import struct
import json

# import threading

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

# lowest and highest desk height in mm
BASE_HEIGHT = 620
MAX_HEIGHT = 1270

# GATT characteristic
UUID_HEIGHT = "99fa0021-338a-1024-8a49-009c0215f78a"
UUID_COMMAND = "99fa0002-338a-1024-8a49-009c0215f78a"
UUID_REFERENCE_INPUT = "99fa0031-338a-1024-8a49-009c0215f78a"

# command definitions
COMMAND_UP = bytearray(struct.pack("<H", 71))
COMMAND_DOWN = bytearray(struct.pack("<H", 70))
COMMAND_STOP = bytearray(struct.pack("<H", 255))
COMMAND_WAKEUP = bytearray(struct.pack("<H", 254))

COMMAND_REFERENCE_INPUT_STOP = bytearray(struct.pack("<H", 32769))
COMMAND_REFERENCE_INPUT_UP = bytearray(struct.pack("<H", 32768))
COMMAND_REFERENCE_INPUT_DOWN = bytearray(struct.pack("<H", 32767))

# config
DEFAULT_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")


# helper functions
def mm_to_raw(mm):
    """Convert a desk height in millimeters to a raw desk height value."""
    return (mm - BASE_HEIGHT) * 10


def raw_to_mm(raw):
    """Convert a raw desk height value to millimeters."""
    return (raw / 10) + BASE_HEIGHT


class Desk:
    """desk model"""

    def __init__(self):

        self.config = self.load_config()
        self.device = None
        self.client = None
        self.subscribed = False
        self.desk_height = 0
        self.desk_speed = 0

    def load_config(self, config_file="desk_config.json"):
        """load config file"""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            return {
                "mac_address": config.get("mac_address", "FD:46:77:A9:30:CA"),
                "adapter_name": config.get("adapter_name", "hci0"),
                "position_3": config.get("position_3", BASE_HEIGHT + 530),
                "position_2": config.get("position_2", BASE_HEIGHT + 430),
                "position_1": config.get("position_1", BASE_HEIGHT + 80),
                "height_tolerance": config.get("height_tolerance", 1),
                "scan_timeout": config.get("scan_timeout", 5),
                "connection_timeout": config.get("connection_timeout", 5),
                "movement_timeout": config.get("movement_timeout", 5),
            }
        except FileNotFoundError:
            return {
                "mac_address": "FD:46:77:A9:30:CA",
                "adapter_name": "hci0",
                "position_3": BASE_HEIGHT + 530,
                "position_2": BASE_HEIGHT + 430,
                "position_1": BASE_HEIGHT + 80,
                "height_tolerance": 1,
                "scan_timeout": 5,
                "connection_timeout": 5,
                "movement_timeout": 5,
            }

    async def scan(self, mac_address):
        """find the device"""
        print(f"Scanning: mac_addr {mac_address}")

        device = await BleakScanner.find_device_by_address(mac_address)

        if device is None:
            print(f"could not find device with address {mac_address}")
            raise BleakError

        print(f"device {device.name} is found...")
        self.device = device

    async def connect(self, attempt=5):
        """connect to the device"""
        if self.device is None:
            print("there is no device to connect to, please find device first...")
            return None
        try:
            print(f"connecting to {self.device.name} with {attempt} times remained")
            if self.client is None:
                self.client = BleakClient(self.device)
            if not self.client.is_connected:
                await self.client.connect(timeout=attempt)
            print(f"connected {self.client.address}")
            return True
        except BleakError as err:
            if attempt != 0:
                await self.connect(attempt=attempt - 1)
            else:
                print(f"connection failure: {err}")
                return False

    async def disconnect(self):
        """disconnecting the client"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("disconnected...")

    async def _get_height_data_from_notification(self, _, data, *, callback):
        """call back function for height notification"""
        height, speed = struct.unpack("<Hh", data)
        # print(f"get_height_data_from_notification: {threading.current_thread()}")
        self.desk_height = int(raw_to_mm(height))
        self.desk_speed = speed
        callback(f"Height: {self.desk_height}; Speed: {self.desk_speed}")
        # loop = asyncio.get_running_loop()
        # await loop.run_in_executor(
        #     None, call_back_func, f"Height: {int(raw_to_mm(height))}"
        # )

    async def subscribe(self, uuid, callback):
        """Listen for notifications on a characteristic"""
        if self.client and self.client.is_connected and not self.subscribed:
            await self.client.start_notify(uuid, callback)
        print(f"callback: {callback.func.__name__} subscribed to client {self.client}")
        self.subscribed = True

    async def unsubscribe(self, uuid):
        """Stop listenening for notifications on a characteristic"""
        if self.client and self.client.is_connected and self.subscribed:
            await self.client.stop_notify(uuid)
            print("unsubscribed...")
            self.subscribed = False

    async def wake_up(self):
        """wake up the client"""
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(UUID_COMMAND, COMMAND_WAKEUP)

    async def stop_move(self):
        """stop moving"""
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(UUID_COMMAND, COMMAND_STOP)
            await self.client.write_gatt_char(
                UUID_REFERENCE_INPUT, COMMAND_REFERENCE_INPUT_STOP
            )

    # async def get_height(client):
    #     """retrieve height by reading height GATT char"""
    #     if client.is_connected:
    #         try:
    #             raw_height, speed = struct.unpack(
    #                 "<Hh", await client.read_gatt_char(UUID_HEIGHT)
    #             )
    #             height = raw_to_mm(raw_height)
    #             return height, speed
    #         except struct.error as err:
    #             print(err)

    # async def move_up(client):
    #     """move desk up"""
    #     try:
    #         await client.write_gatt_char(UUID_COMMAND, COMMAND_UP)
    #     except BleakError as err:
    #         print(err)

    # async def move_down(client):
    #     """move desk down"""
    #     try:
    #         await client.write_gatt_char(UUID_COMMAND, COMMAND_DOWN)
    #     except BleakError as err:
    #         print(err)

    async def move_to_target(self, target):
        """move desk to target by writting GATT char"""
        try:
            if self.client and self.client.is_connected:
                encoded_target = bytearray(struct.pack("<H", int(mm_to_raw(target))))
                # print(f'move_to start: {threading.current_thread()}')
                await self.client.write_gatt_char(UUID_REFERENCE_INPUT, encoded_target)
                # print(f'move_to end: {threading.current_thread()}')
        except BleakError as err:
            print(err)

    async def move_desk_to_target(self, target):
        """move desk to the target by keeping calling move_to function"""
        await self.wake_up()
        await self.stop_move()

        while True:
            # print(f'move_desk start: {threading.current_thread()}')
            await self.move_to_target(target)
            # print(f'move_desk end: {threading.current_thread()}')
            await asyncio.sleep(0.2)

            # print(f"height: {self.desk_height}; speed: {self.desk_speed}")
            if self.desk_speed == 0:
                break

        print(f"Current height: {self.desk_height}")
        print(f"Target height: {target}")

        if int(self.desk_height) != target:
            return False
        return True

    async def move_desk_to_position(self, position, call_back_func):
        """move desk controller"""
        if self.client and self.client.is_connected and not self.subscribed:
            await self.subscribe(
                UUID_HEIGHT,
                functools.partial(
                    self._get_height_data_from_notification, callback=call_back_func
                ),
            )

            success = False
            timeout = self.config["movement_timeout"]
            try:
                while not success and timeout > 0:
                    success = await self.move_desk_to_target(self.config[position])
                    print(
                        f"success: {success}, timeout: {timeout} connection: {self.client.is_connected}"
                    )
                    timeout -= 1

            except (BleakError, asyncio.TimeoutError) as err:
                print(f"Error: {err}")
                print("move error")
            finally:
                if self.client and self.client.is_connected:
                    await self.stop_move()
                    await self.unsubscribe(UUID_HEIGHT)
                    call_back_func("Done")


def log_msg(msg):
    """call back function to print msg"""
    print(msg)


async def main(desk):
    """main function"""
    await desk.scan(desk.config["mac_address"])
    await desk.connect()

    await desk.move_desk_to_position("position_3", log_msg)
    await asyncio.sleep(0.1)
    await desk.move_desk_to_position("position_2", log_msg)

    await desk.disconnect()


if __name__ == "__main__":

    ikea_desk = Desk()
    asyncio.run(main(ikea_desk))
