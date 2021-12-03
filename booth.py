#!/usr/bin/python3

from __future__ import print_function

import logging
import os
from os import listdir
from os.path import isfile, join
import sys
import time
from datetime import datetime
import socket
import requests

import colorama

try:
    from PIL import Image, ImageOps
except ImportError:
    print("installing Pillow")
    from pip._internal import main as pip
    pip(['install', '--user', 'Pillow'])

try:
    from webdav3.client import Client
except ImportError:
    print("installing webdavclient3")
    from pip._internal import main as pip
    pip(['install', '--user', 'webdavclient3'])

try:
    import gphoto2 as gp
except ImportError:
    print("Install it with: sudo apt install python3-gphoto2")


import settings


from rich.console import Console
from rich.logging import RichHandler
console = Console(record=True)
date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")

if settings.ON_RASPI:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("installing RPi.GPIO")
        from pip._internal import main as pip
        pip(['install', '--user', 'RPi.GPIO'])


def take_pictures(number_of_pictures=settings.PICTURES):
    console.line()
    console.rule("[bold green] Taking Pictures")
    date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
    start_delay()
    if settings.DRY_RUN:
        for i in range(number_of_pictures):
            console.log('Generating dummy image')
            img = Image.new('RGB',(2000,1500))
            img.save(f'img/test_{i}.png')
    else:
        try:    
            camera = gp.Camera()
            camera.init()
            for i in range(number_of_pictures):
                console.log('Capturing image')
                file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
                console.log('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
                target = os.path.join('img', file_path.name)
                console.log('Copying image to', target)
                camera_file = camera.file_get(
                    file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
                camera_file.save(target)
                time.sleep(settings.INTERVAL)
            camera.exit()
        except gp.GPhoto2Error:
            console.log("Could not detect any camera")
            console.save_text(f'logs/{date}.text')
            sys.exit(1)

def merge_images(basewidth=settings.BASEWITH, 
                outer_margin=settings.OUTER_MARGIN, 
                inner_margin=settings.INNER_MARGIN,
                bottom_margin=settings.BOTTOM_MARGIN,
                logo=settings.LOGO):
    console.rule("[bold green] Merging Images")
    imgs = list_files('img')

    num_imgs = len(imgs)
    cols = 1
    rows = num_imgs

    if num_imgs % 3 == 0:
        cols = 3
        rows = int(num_imgs/3)

    elif num_imgs % 2 == 0:
        cols = 2
        rows = int(num_imgs/2)

    rotated = []
    for img in imgs:
        i_t = Image.open(img)
        i_t.thumbnail((basewidth, basewidth), Image.ANTIALIAS)
        rotated.append(ImageOps.exif_transpose(i_t))
    
    try:
        image1_size = rotated[0].size
    except IndexError as e:
        console.log(e)
        console.save_text(f'logs/{date}.text')
        sys.exit(1)


    width = int(cols*image1_size[0]+2*outer_margin+(cols-1)*inner_margin)
    height = int(rows*image1_size[1]+outer_margin+(rows-1)*inner_margin+bottom_margin)

    new_image = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    logo_image = Image.new('RGBA', (width, height), (0, 0, 0,0))

    ix = 0
    for i in range(cols):
        for j in range(rows):
            x = int(outer_margin+i*(inner_margin+image1_size[0]))
            y = int(outer_margin+(j)*(inner_margin+image1_size[1]))
            console.log(f"pasting: {rotated[ix]}({ix}) at {x},{y}")
            new_image.paste(rotated[ix], (x, y))
            ix += 1
    lg=Image.open(logo)

    logo_image.paste(lg,(width-outer_margin-lg.width,height-lg.height-inner_margin))
    Image.alpha_composite(new_image,logo_image).save("output/merged_image.png", "PNG")

def list_files(directory):
    return [join(directory, f) for f in listdir(directory) if isfile(join(directory, f))]

def upload(directory=settings.WEBDAV_DIR):
    console.line()
    console.rule("[bold green] Uploading Image")
    try:
        webdav_client = Client(settings.WEBDAV_OPTIONS)
        webdav_client.mkdir(directory)
        console.log(f"uploading img_{date}.png")
        webdav_client.upload_sync(remote_path=f"{directory}/img_{date}.png", local_path="output/merged_image.png")
    except socket.gaierror as e:
        console.log(e)
        console.save_text(f'logs/{date}.text')
        sys.exit(2)
    except requests.exceptions.ConnectionError as e: 
        console.log(e)
        console.save_text(f'logs/{date}.text')
        sys.exit(2)

def clean():
    console.line()
    console.rule("[bold green] Cleaning up")
    [os.remove(f) for f in list_files('img')]
    [os.remove(f) for f in list_files('output')]

def start_delay(delay=settings.DELAY):
    if settings.ON_RASPI:
        for i in range(6):
            GPIO.output(settings.LED_PIN, not GPIO.input(settings.LED_PIN))
            time.sleep(delay/10)
        for i in range(6):
            GPIO.output(settings.LED_PIN, not GPIO.input(settings.LED_PIN))
            time.sleep(delay/20)
    else:
        time.sleep(delay)

def main():
    
    FORMAT = "%(message)s"
    logging.basicConfig(
        level=logging.WARNING, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    log = logging.getLogger("rich")
    callback_obj = gp.check_result(gp.use_python_logging())
    
    if settings.ON_RASPI:
        GPIO.setwarnings(False) 
        GPIO.setmode(GPIO.BCM) 
        GPIO.setup(settings.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(settings.LED_PIN, GPIO.OUT)
        GPIO.output(settings.LED_PIN, GPIO.HIGH)

        # GPIO.add_event_detect(settings.BUTTON_PIN,GPIO.FALLING,callback=button_callback,bouncetime=settings.BOUNCETIME)
        GPIO.add_event_detect(settings.BUTTON_PIN,GPIO.FALLING)
        console.line()
        console.rule("[bold yellow] photobooth Ready....")
        GPIO.output(settings.LED_PIN,GPIO.LOW)

        while True:
            try:
                time.sleep(0.25)
                if GPIO.event_detected(settings.BUTTON_PIN):
                    console.log("Button Pressed")
                    GPIO.remove_event_detect(settings.BUTTON_PIN)
                    GPIO.output(settings.LED_PIN,GPIO.HIGH)
                    take_pictures()
                    merge_images()
                    upload()
                    clean()
                    GPIO.add_event_detect(settings.BUTTON_PIN, GPIO.FALLING)
                    GPIO.output(settings.LED_PIN,GPIO.LOW)
            except KeyboardInterrupt:
                console.line()
                console.rule("[bold red] photobooth Stopped")
                GPIO.cleanup()  
                sys.exit(0)



    else:
        take_pictures()
        merge_images()
        upload()
        clean()
        if settings.LOGGING:
            console.save_text(f'logs/{date}.text')


if __name__ == "__main__":
    sys.exit(main())
