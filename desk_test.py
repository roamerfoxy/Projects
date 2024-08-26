import argparse
import asyncio
import functools
import json
import os
import pickle
import shutil
import struct
import sys
import time

import yaml
from appdirs import user_config_dir
from bleak import BleakClient, BleakError, BleakScanner

# lowest and highest desk height in mm
BASE_HEIGHT = 620
MAX_HEIGHT = 1270

# GATT characteristic
UUID_HEIGHT = '99fa0021-338a-1024-8a49-009c0215f78a'
UUID_COMMAND = '99fa0002-338a-1024-8a49-009c0215f78a'
UUID_REFERENCE_INPUT = '99fa0031-338a-1024-8a49-009c0215f78a'

# command definitions
COMMAND_UP = bytearray(struct.pack("<H", 71))
COMMAND_DOWN = bytearray(struct.pack("<H", 70))
COMMAND_STOP = bytearray(struct.pack("<H", 255))

COMMAND_REFERENCE_INPUT_STOP = bytearray(struct.pack("<H", 32769))
COMMAND_REFERENCE_INPUT_UP = bytearray(struct.pack("<H", 32768))
COMMAND_REFERENCE_INPUT_DOWN = bytearray(struct.pack("<H", 32767))

# helper functions

# config
DEFAULT_CONFIG_DIR = user_config_dir('idasen-controller')
PICKLE_FILE = os.path.join(DEFAULT_CONFIG_DIR, 'desk.pickle.test')

config = {
    "mac_address": 'FD:46:77:A9:30:CA',
    "stand_height1": BASE_HEIGHT + 430,
    "stand_height2": BASE_HEIGHT + 530,
    "sit_height": BASE_HEIGHT + 100,
    "height_tolerance": 20.0,
    "adapter_name": 'hci0',
    "scan_timeout": 5,
    "connection_timeout": 10,
    "movement_timeout": 30,
}


async def scan(mac_address=None):
    print("Scanning")
    scanner = BleakScanner()
    try:
        devices = await scanner.discover(timeout=config['connection_timeout'])
    except Exception as e:
        print(e)
    if not mac_address:
        print('Found {} devices using {}'.format(
            len(devices), config['adapter_name']))
        for device in devices:
            print(device)
        return devices
    for device in devices:
        if device.address == mac_address:
            print('Scanning - desk {} found'.format(device.name))
            return device
    print('Scanning - desk {} not found'.format(mac_address))
    return None


async def connect(client=None, attempt=0):
    desk = unpickle_desk()
    if not desk:
        desk = await scan(config['mac_address'])
        if not desk:
            print('Could not find desk {}'.format(config['mac_address']))
            return None
        else:
            pickle_desk(desk)
    try:
        print('connecting {}'.format(desk))
        if not client:
            client = BleakClient(desk, device=config['adapter_name'])
        await client.connect(timeout=config['connection_timeout'])
        print('connected {}'.format(desk))
        return client
    except BleakError as e:
        if attempt != 0:
            return await connect(attempt=attempt - 1)
        else:
            print('connecting failed')
            print(e)
            return None


async def disconnect(client):
    if client.is_connected:
        await client.disconnect()


def unpickle_desk():
    """Load a Bleak device config from a pickle file and check that it is the correct device"""
    try:
        with open(PICKLE_FILE, 'rb') as f:
            desk = pickle.load(f)
            if desk.address == config['mac_address']:
                return desk
    except Exception:
        print('error to unpickle desk')
    return None


def pickle_desk(desk):
    """Attempt to pickle the desk"""
    try:
        with open(PICKLE_FILE, 'wb') as f:
            pickle.dump(desk, f)
    except Exception as e:
        print('error to pickle desk: {}'.format(e))


async def stop(client):
    await client.write_gatt_char(UUID_COMMAND, COMMAND_STOP)
    await client.write_gatt_char(UUID_REFERENCE_INPUT, COMMAND_REFERENCE_INPUT_STOP)


async def get_height(client):
    if client.is_connected:
        raw_height, speed = struct.unpack('<Hh', await client.read_gatt_char(UUID_HEIGHT))
        # 10 raw_height = 1MM
        height = raw_height / 10 + BASE_HEIGHT
        return height, speed


async def move_up(client):
    try:
        await client.write_gatt_char(UUID_COMMAND, COMMAND_UP)
    except Exception as e:
        print(e)


async def move_down(client):
    try:
        res = await client.write_gatt_char(UUID_COMMAND, COMMAND_DOWN)
    except Exception as e:
        print(e)


async def move_to_target(client, target):
    inital_height, _ = await get_height(client)
    direction = 'UP' if inital_height < target else 'DOWN'
    pre_height = inital_height

    while True:
        current_height, speed = await get_height(client)

        if (direction == 'UP' and current_height < pre_height) or (direction == 'DOWN' and current_height > pre_height):
            break

        difference = target - current_height

        if (difference < 0 and direction == 'UP') or (difference > 0 and direction == 'DOWN'):
            print('overshooted')
            await stop(client)
            return True

        if abs(difference) < config['height_tolerance']:
            print('reached height: {} MM'.format(target))
            await stop(client)
            return True
        elif difference > 0:
            await move_up(client)
            print(f'current height: {current_height}')
        elif difference < 0:
            await move_down(client)
            print(f'current height: {current_height, speed}')

        pre_height = current_height

    return False


async def position_one():
    try:
        client = await connect()
        await move_to_target(client, config['stand_height2'])
    except Exception:
        print('move error')
    finally:
        if client:
            await stop(client)
            await disconnect(client)
            print('disconnected')


async def position_two():
    try:
        client = await connect()
        await move_to_target(client, config['stand_height1'])
    except Exception:
        print('move error')
    finally:
        if client:
            await stop(client)
            await disconnect(client)
            print('disconnected')


async def position_three():
    try:
        client = await connect()
        await move_to_target(client, config['sit_height'])
    except Exception:
        print('move error')
    finally:
        if client:
            await stop(client)
            await disconnect(client)
            print('disconnected')


async def main(arg):
    try:
        client = await connect()

        if arg.stand:
            await move_to_target(client, config['stand_height2'])
        elif arg.sit:
            success = False
            while (not success):
                success = await move_to_target(client, config['sit_height'])
        else:
            await move_to_target(client, config['stand_height1'])
    except Exception as e:
        print(e)
        print('move error')
    finally:
        if client:
            await stop(client)
            await disconnect(client)
            print('disconnected')


def init():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sit', action='store_true')
    parser.add_argument('--stand', action='store_true')
    arg = parser.parse_args()

    try:
        asyncio.run(main(arg))
    except Exception:
        pass


def set_pos_one():
    try:
        asyncio.run(position_one)
        time.sleep(3)
    except Exception:
        pass


def set_pos_two():
    try:
        asyncio.run(position_two)
        time.sleep(3)
    except Exception:
        pass


def set_pos_three():
    try:
        asyncio.run(position_three)
        time.sleep(3)
    except Exception:
        pass


if __name__ == "__main__":
    init()
