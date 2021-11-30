from __future__ import print_function
from PIL import Image, ImageOps

import logging
import os
from os import listdir
from os.path import isfile, join
import sys
import time

import gphoto2 as gp

BASEWITH = 500
PICTURES = 9
INTERVAL = 1


def take_pictures(number_of_pictures):
    camera = gp.Camera()
    camera.init()
    for i in range(number_of_pictures):
        print('Capturing image')
        file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
        print(
            'Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
        target = os.path.join('img', file_path.name)
        print('Copying image to', target)
        camera_file = camera.file_get(
            file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
        camera_file.save(target)
        time.sleep(INTERVAL)
    camera.exit()


def merge_images(basewidth=800, outer_margin=20, inner_margin=10,bottom_margin=80,logo='logo/logo.png'):

    imgs = ['img/'+f for f in listdir('img') if isfile(join('img', f))]

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
        print(f'Column {i}')
        for j in range(rows):
            print(f'Row {j}')
            x = int(outer_margin+i*(inner_margin+image1_size[0]))
            y = int(outer_margin+(j)*(inner_margin+image1_size[1]))
            print(f"pasting: {rotated[ix]}({ix}) at {x},{y}")
            new_image.paste(rotated[ix], (x, y))
            ix += 1
    lg=Image.open(logo)

    logo_image.paste(lg,(width-outer_margin-lg.width,height-lg.height-inner_margin))
    Image.alpha_composite(new_image,logo_image).save("output/merged_image.png", "PNG")


def main():
    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    callback_obj = gp.check_result(gp.use_python_logging())

    take_pictures(PICTURES)
    merge_images()

    return 0


if __name__ == "__main__":
    sys.exit(main())
