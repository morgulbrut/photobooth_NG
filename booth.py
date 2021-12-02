from __future__ import print_function


import logging
import os
from os import listdir
from os.path import isfile, join
import sys
import time
from datetime import datetime

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
console = Console()


if settings.ON_RASPI:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("installing RPi.GPIO")
        from pip._internal import main as pip
        pip(['install', '--user', 'RPi.GPIO'])


def take_pictures(number_of_pictures=settings.PICTURES):
    console.rule("[bold breen] Taking Pictures")
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


def merge_images(basewidth=settings.BASEWITH, 
                outer_margin=settings.OUTER_MARGIN, 
                inner_margin=settings.INNER_MARGIN,
                bottom_margin=settings.BOTTOM_MARGIN,
                logo=settings.LOGO):
    console.rule("[bold breen] Merging Images")
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

    image1_size = rotated[0].size

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
    console.rule("[bold green] Uploading Image")
    webdav_client = Client(settings.WEBDAV_OPTIONS)
    webdav_client.mkdir(directory)
    date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
    console.log(f"uploading img_{date}.png")
    webdav_client.upload_sync(remote_path=f"{directory}/img_{date}.png", local_path="output/merged_image.png")

def clean():
    console.rule("[bold green] Cleaning up")
    [os.remove(f) for f in list_files('img')]
    [os.remove(f) for f in list_files('output')]


'''Only used when running on a RasPi'''
def button_callback(channel):
    console.log("Button was pushed!")        
    take_pictures()
    merge_images()
    upload()
    clean()

def main():
    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    callback_obj = gp.check_result(gp.use_python_logging())

    if settings.ON_RASPI:  
        GPIO.setwarnings(False) # Ignore warning for now
        GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
        GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
        GPIO.add_event_detect(10,GPIO.Falling,callback=button_callback) # Setup event on pin 10 rising edge
        message = input("Press enter to quit\n\n") # Run until someone presses enter
        GPIO.cleanup() # Clean up

    else:    
        take_pictures()
        merge_images()
        upload()
        clean()

if __name__ == "__main__":
    sys.exit(main())


