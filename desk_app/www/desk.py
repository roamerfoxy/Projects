"""desk model"""

import functools
import asyncio
import os
import struct

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError, BleakDBusError

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


# helper functions
def mm_to_raw(mm):
    return (mm - BASE_HEIGHT) * 10


def raw_to_mm(raw):
    return (raw / 10) + BASE_HEIGHT


# config
DEFAULT_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")

config = {
    "mac_address": "FD:46:77:A9:30:CA",
    "position_3": BASE_HEIGHT + 530,
    "position_2": BASE_HEIGHT + 430,
    "position_1": BASE_HEIGHT + 80,
    "height_tolerance": 20.0,
    "adapter_name": "hci0",
    "scan_timeout": 5,
    "connection_timeout": 5,
    "movement_timeout": 5,
}


async def scan(mac_address=None):
    print("Scanning")

    if mac_address:
        device = await BleakScanner.find_device_by_address(config["mac_address"],config["connection_timeout"])

        if device is None:
            print(f'could not find device with address {config[mac_address]}')
            raise BleakError
        
        return device

    # try:
    #     devices = await scanner.discover(timeout=config["connection_timeout"])
    # except BleakError as err:
    #     print(err)
    # if not mac_address:
    #     print("Found {} devices using {}".format(len(devices), config["adapter_name"]))
    #     for device in devices:
    #         print(device)
    #     return devices
    # for device in devices:
    #     if device.address == mac_address:
    #         print("Scanning - desk {} found".format(device.name))
    #         return device
    # print("Scanning - desk {} not found".format(mac_address))
    # return None


async def connect(client=None, attempt=0):
    try:
        print(f"connecting to {config['mac_address']} with {attempt} times remained")
        if not client:
            client = BleakClient(config["mac_address"])
        await client.connect(timeout=config["connection_timeout"])
        print("connected {}".format(client.address))
        return client
    except BleakError as err:
        if attempt != 0:
            return await connect(attempt=attempt - 1)
        else:
            print("connecting failed")
            print(err)
            return None


async def disconnect(client):
    """disconnecting the client"""
    if client.is_connected:
        await client.disconnect()


async def get_height_data_from_notification(_, data, *, call_back_func):
    """call back function for height notification"""
    height, _ = struct.unpack("<Hh", data)
    await call_back_func(f"Height: {int(raw_to_mm(height))}")


async def subscribe(client, uuid, callback):
    """Listen for notifications on a characteristic"""
    await client.start_notify(uuid, callback)
    print(f"callback: {callback.func.__name__} subscribed to client {client}")


async def unsubscribe(client, uuid):
    """Stop listenening for notifications on a characteristic"""
    await client.stop_notify(uuid)


async def wake_up(client):
    """wake up the client"""
    await client.write_gatt_char(UUID_COMMAND, COMMAND_WAKEUP)


async def stop(client):
    """stop moving"""
    await client.write_gatt_char(UUID_COMMAND, COMMAND_STOP)
    await client.write_gatt_char(UUID_REFERENCE_INPUT, COMMAND_REFERENCE_INPUT_STOP)


async def get_height(client):
    """retrieve height by reading height GATT char"""
    if client.is_connected:
        try:
            raw_height, speed = struct.unpack(
                "<Hh", await client.read_gatt_char(UUID_HEIGHT)
            )
            height = raw_to_mm(raw_height)
            return height, speed
        except Exception as err:
            print(err)


async def move_up(client):
    """move desk up"""
    try:
        await client.write_gatt_char(UUID_COMMAND, COMMAND_UP)
    except BleakError as err:
        print(err)


async def move_down(client):
    """move desk down"""
    try:
        await client.write_gatt_char(UUID_COMMAND, COMMAND_DOWN)
    except BleakError as err:
        print(err)


async def move_to(client, target):
    """move desk to target by writting GATT char"""
    try:
        encoded_target = bytearray(struct.pack("<H", int(mm_to_raw(target))))
        await client.write_gatt_char(UUID_REFERENCE_INPUT, encoded_target)
    except BleakError as err:
        print(err)


async def move_desk_to_target(client, target):
    """move desk to the target by keeping calling move_to function"""
    await wake_up(client)
    await stop(client)

    current_height = 0
    speed = 0

    while True:
        await move_to(client, target)
        await asyncio.sleep(0.2)

        result = await get_height(client)
        if result:
            (current_height, speed) = result
        else:
            print("get_height function return None")
            speed = 0

        if speed == 0:
            break

    print(f"Current height: {int(current_height)}")
    print(f"Target height: {int(target)}")

    if int(current_height) != target:
        return False
    return True


async def move_desk(position, call_back_func):
    """move desk controller"""

    device = await BleakScanner.find_device_by_address(config["mac_address"], config["connection_timeout"])

    if device is None:
        print(f'could not find device with address {config["mac_address"]}')
        raise BleakError

    client = await connect(BleakClient(device), config["connection_timeout"])

    if client:
        await subscribe(
            client,
            UUID_HEIGHT,
            functools.partial(
                get_height_data_from_notification, call_back_func=call_back_func
            ),
        )

        success = False
        timeout = config["movement_timeout"]
        try:
            while not success and timeout > 0:
                success = await move_desk_to_target(client, config[position])
                print(
                    f"success: {success}, timeout: {timeout} connection: {client.is_connected}"
                )
                timeout -= 1

        except BleakError as err:
            print(err)
            print("move error")
        finally:
            if client and client.is_connected:
                await stop(client)
                await unsubscribe(client, UUID_HEIGHT)
                await disconnect(client)




stand = functools.partial(move_desk, "position_2")
sit = functools.partial(move_desk, "position_1")

if __name__ == "__main__":

    async def log_msg(msg):
        """call back function to print msg"""
        print(msg)

    asyncio.run(stand(log_msg))
