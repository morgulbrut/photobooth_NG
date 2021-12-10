#!/usr/bin/python3

import serial
import settings
import time

flash = serial.Serial()
flash.baudrate = 115200
flash.port = settings.RINGLIGHT_PORT
flash.open()

flash.write(settings.RINGLIGHT_ON)
time.sleep(.5)
flash.write(settings.RINGLIGHT_OFF)

